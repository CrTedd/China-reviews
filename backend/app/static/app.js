/* ============================================================
   Фронтенд SPA для агрегатора рейтингов.
   Чистый JS, без зависимостей. Маршрутизация по хэшу.
   ============================================================ */

const App = (() => {
  // ---------- Состояние ----------
  const state = {
    token: localStorage.getItem("cr_token") || null,
    user: null,
    refs: { platforms: [], categories: [], sellers: [], products: [] },
  };

  // ---------- Утилиты ----------
  const $ = (sel, root = document) => root.querySelector(sel);
  const el = (html) => {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  };
  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  const fmtDate = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
  };

  const stars = (val) => {
    if (val == null) return "";
    const full = Math.round(val);
    return "★".repeat(full) + "☆".repeat(Math.max(0, 5 - full));
  };

  function toast(msg, type = "") {
    const box = $("#toasts");
    const t = el(`<div class="toast ${type}">${esc(msg)}</div>`);
    box.appendChild(t);
    setTimeout(() => {
      t.style.opacity = "0";
      setTimeout(() => t.remove(), 250);
    }, 3000);
  }

  // ---------- API-клиент ----------
  async function api(path, { method = "GET", body, form, auth = false } = {}) {
    const headers = {};
    let payload;
    if (form) {
      payload = new URLSearchParams(form).toString();
      headers["Content-Type"] = "application/x-www-form-urlencoded";
    } else if (body !== undefined) {
      payload = JSON.stringify(body);
      headers["Content-Type"] = "application/json";
    }
    if (auth && state.token) headers["Authorization"] = "Bearer " + state.token;

    const res = await fetch(path, { method, headers, body: payload });
    let data = null;
    const text = await res.text();
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
    if (!res.ok) {
      const detail = (data && data.detail) ? data.detail : `Ошибка ${res.status}`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  }

  // ---------- Аутентификация ----------
  function setToken(token) {
    state.token = token;
    if (token) localStorage.setItem("cr_token", token);
    else localStorage.removeItem("cr_token");
  }

  async function loadMe() {
    if (!state.token) { state.user = null; return; }
    try { state.user = await api("/users/me", { auth: true }); }
    catch { setToken(null); state.user = null; }
  }

  function requireAuth() {
    if (!state.user) {
      toast("Сначала войдите в систему", "err");
      location.hash = "#/auth";
      return false;
    }
    return true;
  }

  // ---------- Справочники ----------
  async function loadRefs() {
    try {
      const [platforms, categories, sellers, products] = await Promise.all([
        api("/platforms"), api("/categories"), api("/sellers"), api("/products?limit=300"),
      ]);
      state.refs = { platforms, categories, sellers, products };
    } catch (e) { /* справочники не критичны для просмотра */ }
  }

  // ---------- Навигация ----------
  function syncNav() {
    const route = (location.hash.replace("#/", "").split("/")[0]) || "search";
    document.querySelectorAll(".nav a").forEach((a) =>
      a.classList.toggle("active", a.dataset.route === route)
    );
    const link = $("#authLink");
    if (state.user) {
      link.textContent = "Выйти (" + (state.user.display_name || state.user.email) + ")";
      link.dataset.route = "logout";
      link.setAttribute("href", "#/logout");
    } else {
      link.textContent = "Войти";
      link.dataset.route = "auth";
      link.setAttribute("href", "#/auth");
    }
  }

  // ============================================================
  //  ЭКРАНЫ
  // ============================================================

  // ---- Поиск + рекомендации ----
  function viewSearch(root) {
    root.innerHTML = `
      <div class="page-head">
        <div><h1>Поиск отзывов</h1>
        <p>Рекомендательное ранжирование по релевантности, баллам и свежести</p></div>
      </div>
      <div class="card">
        <div class="search-bar">
          <div class="grow">
            <input id="q" placeholder="Например: наушники, смарт-часы, кабель..." />
          </div>
          <button class="btn" id="goBtn">Найти</button>
        </div>
        <div class="controls">
          <div>
            <select id="category"><option value="">Все категории</option></select>
          </div>
          <div>
            <select id="sort">
              <option value="relevance">Сортировка: по релевантности</option>
              <option value="score">Сортировка: по баллам</option>
              <option value="date">Сортировка: по дате</option>
            </select>
          </div>
          <div>
            <select id="order">
              <option value="desc">По убыванию</option>
              <option value="asc">По возрастанию</option>
            </select>
          </div>
        </div>
      </div>
      <div id="results"></div>
    `;

    const catSel = $("#category", root);
    state.refs.categories.forEach((c) =>
      catSel.appendChild(el(`<option value="${esc(c.name)}">${esc(c.name)}</option>`))
    );

    async function run() {
      const box = $("#results", root);
      box.innerHTML = `<div class="spinner"></div>`;
      const params = new URLSearchParams({
        q: $("#q", root).value,
        category: $("#category", root).value,
        sort: $("#sort", root).value,
        order: $("#order", root).value,
        limit: "30",
      });
      if (state.token) params.set("authorization", state.token);
      try {
        const data = await api("/search?" + params.toString());
        renderResults(box, data.results);
      } catch (e) {
        box.innerHTML = `<div class="empty">Не удалось загрузить: ${esc(e.message)}</div>`;
      }
    }

    function renderResults(box, items) {
      if (!items.length) {
        box.innerHTML = `<div class="empty">Ничего не найдено. Измените запрос или категорию.</div>`;
        return;
      }
      box.innerHTML = "";
      items.forEach((x) => {
        const card = el(`
          <a class="result" href="#/review/${x.review_id}">
            <div class="result-top">
              <span class="result-title">${esc(x.product_title)}</span>
              <span class="score-pill"><span class="stars">${stars(x.score_total)}</span>
                ${x.score_total != null ? x.score_total.toFixed(2) : "—"}</span>
            </div>
            <div class="badges">
              ${x.category ? `<span class="badge">${esc(x.category)}</span>` : ""}
              ${x.platform ? `<span class="badge brand">${esc(x.platform)}</span>` : ""}
              ${x.seller ? `<span class="badge">${esc(x.seller)}</span>` : ""}
              <span class="metric">rank ${x.rank}</span>
              <span class="metric">релевантность ${x.relevance}</span>
            </div>
            <div class="comment">${esc(x.comment_text || "")}</div>
            <div class="muted" style="font-size:12px;margin-top:6px">${fmtDate(x.created_at)}</div>
          </a>`);
        box.appendChild(card);
      });
    }

    $("#goBtn", root).onclick = run;
    $("#q", root).addEventListener("keydown", (e) => { if (e.key === "Enter") run(); });
    $("#sort", root).onchange = run;
    $("#order", root).onchange = run;
    $("#category", root).onchange = run;
    run();
  }

  // ---- Карточка отзыва + комментарии ----
  async function viewReview(root, id) {
    root.innerHTML = `<div class="spinner"></div>`;
    let review;
    try { review = await api("/reviews/" + id); }
    catch (e) { root.innerHTML = `<div class="empty">Отзыв не найден.</div>`; return; }

    const product = state.refs.products.find((p) => p.id === review.product_id);
    const platform = state.refs.platforms.find((p) => p.id === review.platform_id);
    const seller = state.refs.sellers.find((s) => s.id === review.seller_id);

    root.innerHTML = `
      <div class="page-head">
        <div><h1>${esc(product ? product.title : "Отзыв #" + review.id)}</h1>
        <p>${platform ? esc(platform.name) : ""}${seller ? " · " + esc(seller.name) : ""}</p></div>
        <a class="btn ghost small" href="#/search">К поиску</a>
      </div>

      <div class="card">
        <div class="split" style="justify-content:space-between">
          <div class="score-pill" style="font-size:18px">
            <span class="stars">${stars(review.score_total)}</span>
            ${review.score_total != null ? review.score_total.toFixed(2) : "—"} из 5
          </div>
          <button class="btn small secondary" id="usefulBtn">Отзыв полезен</button>
        </div>
        <div class="divider"></div>
        <div class="grid-2">
          <div>
            <div class="kv"><span>Сервис / площадка</span><b>${review.score_service} / 5</b></div>
            <div class="kv"><span>Продавец</span><b>${review.score_seller} / 5</b></div>
          </div>
          <div>
            <div class="kv"><span>Товар</span><b>${review.score_product} / 5</b></div>
            <div class="kv"><span>Доставка</span><b>${review.score_delivery} / 5</b></div>
          </div>
        </div>
        ${review.comment_text ? `<div class="divider"></div><p>${esc(review.comment_text)}</p>` : ""}
        <div class="muted" style="font-size:12px">${fmtDate(review.created_at)}</div>
      </div>

      <div class="card">
        <h2>Обсуждение</h2>
        <p class="hint">Оставляйте комментарии и отвечайте на них</p>
        <div id="newComment"></div>
        <div id="commentTree"><div class="spinner"></div></div>
      </div>
    `;

    $("#usefulBtn", root).onclick = async () => {
      if (!requireAuth()) return;
      try {
        await api("/feedback", { method: "POST", auth: true, body: { review_id: review.id, is_useful: 1 } });
        toast("Спасибо за оценку полезности", "ok");
      } catch (e) { toast(e.message, "err"); }
    };

    renderCommentForm($("#newComment", root), review.id, null, () => loadComments());

    async function loadComments() {
      const box = $("#commentTree", root);
      box.innerHTML = `<div class="spinner"></div>`;
      try {
        const tree = await api(`/reviews/${review.id}/comments`);
        box.innerHTML = "";
        if (!tree.length) { box.innerHTML = `<div class="empty">Пока нет комментариев. Будьте первым.</div>`; return; }
        tree.forEach((node) => box.appendChild(renderComment(node, review.id, loadComments)));
      } catch (e) {
        box.innerHTML = `<div class="empty">Не удалось загрузить комментарии.</div>`;
      }
    }
    loadComments();
  }

  function renderCommentForm(mount, reviewId, parentId, onDone) {
    mount.innerHTML = "";
    const form = el(`
      <div>
        <textarea placeholder="${parentId ? "Ваш ответ..." : "Ваш комментарий..."}"></textarea>
        <div style="margin-top:8px"><button class="btn small">Отправить</button></div>
      </div>`);
    const ta = $("textarea", form);
    $("button", form).onclick = async () => {
      if (!requireAuth()) return;
      const text = ta.value.trim();
      if (!text) { toast("Введите текст", "err"); return; }
      try {
        await api("/comments", {
          method: "POST", auth: true,
          body: { review_id: reviewId, text, parent_comment_id: parentId },
        });
        ta.value = "";
        toast("Комментарий добавлен", "ok");
        onDone();
      } catch (e) { toast(e.message, "err"); }
    };
    mount.appendChild(form);
  }

  function renderComment(node, reviewId, reload) {
    const wrap = el(`
      <div class="comment-node">
        <div class="comment-body">
          <div class="comment-meta">Пользователь #${node.user_id} · ${fmtDate(node.created_at)}</div>
          <div>${esc(node.text)}</div>
          <span class="reply-link">Ответить</span>
          <div class="reply-mount"></div>
        </div>
        <div class="comment-children"></div>
      </div>`);
    const replyLink = $(".reply-link", wrap);
    const replyMount = $(".reply-mount", wrap);
    let open = false;
    replyLink.onclick = () => {
      open = !open;
      if (open) renderCommentForm(replyMount, reviewId, node.id, reload);
      else replyMount.innerHTML = "";
    };
    const children = $(".comment-children", wrap);
    (node.replies || []).forEach((ch) => children.appendChild(renderComment(ch, reviewId, reload)));
    return wrap;
  }

  // ---- Создание отзыва ----
  function viewNew(root) {
    if (!requireAuth()) { root.innerHTML = ""; return; }
    root.innerHTML = `
      <div class="page-head"><div><h1>Оставить отзыв</h1>
      <p>Оцените заказ по четырём критериям</p></div></div>
      <div class="card">
        <label class="field"><span class="lbl">Товар</span>
          <select id="product"></select></label>
        <div class="row">
          <label class="field"><span class="lbl">Площадка</span>
            <select id="platform"></select></label>
          <label class="field"><span class="lbl">Продавец</span>
            <select id="seller"></select></label>
        </div>
        <div class="divider"></div>
        <div class="grid-2">
          ${criterionBlock("service", "Сервис / площадка")}
          ${criterionBlock("seller", "Продавец")}
          ${criterionBlock("product", "Товар")}
          ${criterionBlock("delivery", "Доставка")}
        </div>
        <label class="field"><span class="lbl">Комментарий (необязательно)</span>
          <textarea id="comment" placeholder="Расскажите о вашем опыте..."></textarea></label>
        <button class="btn" id="submitReview">Опубликовать отзыв</button>
      </div>`;

    fillSelect($("#product", root), state.refs.products, (p) => p.title);
    fillSelect($("#platform", root), state.refs.platforms, (p) => p.name);
    fillSelect($("#seller", root), state.refs.sellers, (s) => s.name);

    const scores = { service: 5, seller: 5, product: 5, delivery: 5 };
    ["service", "seller", "product", "delivery"].forEach((k) =>
      setupStars($(`#stars-${k}`, root), (v) => (scores[k] = v), 5)
    );

    $("#submitReview", root).onclick = async () => {
      const product_id = parseInt($("#product", root).value, 10);
      const platform_id = parseInt($("#platform", root).value, 10);
      const seller_id = parseInt($("#seller", root).value, 10);
      if (!product_id) { toast("Выберите товар", "err"); return; }
      try {
        const rv = await api("/reviews", {
          method: "POST", auth: true,
          body: {
            product_id, platform_id, seller_id,
            score_service: scores.service, score_seller: scores.seller,
            score_product: scores.product, score_delivery: scores.delivery,
            comment_text: $("#comment", root).value,
          },
        });
        toast("Отзыв опубликован", "ok");
        location.hash = "#/review/" + rv.id;
      } catch (e) { toast(e.message, "err"); }
    };
  }

  function criterionBlock(key, label) {
    return `<label class="field"><span class="lbl">${label}</span>
      <div class="star-input" id="stars-${key}"></div></label>`;
  }

  function setupStars(mount, onChange, initial) {
    let value = initial;
    function render() {
      mount.innerHTML = "";
      for (let i = 1; i <= 5; i++) {
        const b = el(`<button type="button" class="${i <= value ? "on" : ""}">★</button>`);
        b.onclick = () => { value = i; onChange(i); render(); };
        mount.appendChild(b);
      }
    }
    render();
  }

  function fillSelect(sel, items, labelFn) {
    sel.innerHTML = "";
    items.forEach((it) => sel.appendChild(el(`<option value="${it.id}">${esc(labelFn(it))}</option>`)));
  }

  // ---- Аналитика ----
  async function viewAnalytics(root) {
    root.innerHTML = `
      <div class="page-head"><div><h1>Аналитика</h1>
      <p>Сводные показатели по отзывам</p></div></div>
      <div class="card"><h2>Средний балл по площадкам</h2>
        <div id="byPlatform"><div class="spinner"></div></div></div>
      <div class="grid-2">
        <div class="card"><h2>Средние по критериям</h2>
          <div id="criteria"><div class="spinner"></div></div></div>
        <div class="card"><h2>Распределение оценок</h2>
          <div id="dist" class="center"><div class="spinner"></div></div></div>
      </div>`;

    try {
      const platforms = await api("/analytics/by-platform");
      renderBars($("#byPlatform", root), platforms.map((p) => ({ label: p.platform, value: p.avg })), 5);
    } catch { $("#byPlatform", root).innerHTML = `<div class="empty">Нет данных</div>`; }

    try {
      const crit = await api("/analytics/criteria-avg");
      renderBars($("#criteria", root), crit.map((c) => ({ label: c.criterion, value: c.avg })), 5);
    } catch { $("#criteria", root).innerHTML = `<div class="empty">Нет данных</div>`; }

    try {
      const dist = await api("/analytics/score-distribution");
      $("#dist", root).innerHTML = "";
      $("#dist", root).appendChild(renderDonut(dist));
    } catch { $("#dist", root).innerHTML = `<div class="empty">Нет данных</div>`; }
  }

  function renderBars(mount, rows, max) {
    mount.innerHTML = "";
    if (!rows.length) { mount.innerHTML = `<div class="empty">Нет данных</div>`; return; }
    rows.forEach((r) => {
      const pct = Math.max(0, Math.min(100, (r.value / max) * 100));
      mount.appendChild(el(`
        <div class="barrow">
          <span class="lbl">${esc(r.label)}</span>
          <span class="track"><span class="fill" style="width:${pct}%"></span></span>
          <span class="val">${r.value}</span>
        </div>`));
    });
  }

  // Пончиковая диаграмма распределения оценок (inline SVG)
  function renderDonut(dist) {
    const colors = ["#c0392b", "#e67e22", "#d9a406", "#7cb342", "#1f9d55"];
    const total = dist.reduce((s, d) => s + d.count, 0) || 1;
    const R = 70, r = 42, cx = 90, cy = 90;
    let angle = -Math.PI / 2;
    let paths = "";
    dist.forEach((d, i) => {
      const frac = d.count / total;
      const a2 = angle + frac * Math.PI * 2;
      const large = frac > 0.5 ? 1 : 0;
      const x1 = cx + R * Math.cos(angle), y1 = cy + R * Math.sin(angle);
      const x2 = cx + R * Math.cos(a2), y2 = cy + R * Math.sin(a2);
      const xi1 = cx + r * Math.cos(a2), yi1 = cy + r * Math.sin(a2);
      const xi2 = cx + r * Math.cos(angle), yi2 = cy + r * Math.sin(angle);
      if (d.count > 0) {
        paths += `<path d="M${x1} ${y1} A${R} ${R} 0 ${large} 1 ${x2} ${y2}
          L${xi1} ${yi1} A${r} ${r} 0 ${large} 0 ${xi2} ${yi2} Z" fill="${colors[i]}"></path>`;
      }
      angle = a2;
    });
    const legend = dist.map((d, i) =>
      `<div><span class="dot" style="background:${colors[i]}"></span>${d.score} баллов — ${d.count}</div>`
    ).join("");
    return el(`
      <div class="split">
        <svg width="180" height="180" viewBox="0 0 180 180" role="img" aria-label="Распределение оценок">
          ${paths}
          <text x="90" y="86" text-anchor="middle" font-size="13" fill="#6b7488">всего</text>
          <text x="90" y="104" text-anchor="middle" font-size="18" font-weight="700" fill="#1b2030">${total}</text>
        </svg>
        <div class="donut-legend">${legend}</div>
      </div>`);
  }

  // ---- Профиль (веса критериев) ----
  async function viewProfile(root) {
    if (!requireAuth()) { root.innerHTML = ""; return; }
    root.innerHTML = `
      <div class="page-head"><div><h1>Профиль</h1>
      <p>Настройте важность критериев для персональных рекомендаций</p></div></div>
      <div class="card">
        <div class="kv"><span>Имя</span><b>${esc(state.user.display_name || "—")}</b></div>
        <div class="kv"><span>Email</span><b>${esc(state.user.email)}</b></div>
      </div>
      <div class="card">
        <h2>Веса критериев</h2>
        <p class="hint">Чем выше вес, тем сильнее критерий влияет на рекомендации (сумма нормализуется автоматически)</p>
        ${weightRow("service", "Сервис / площадка")}
        ${weightRow("seller", "Продавец")}
        ${weightRow("product", "Товар")}
        ${weightRow("delivery", "Доставка")}
        <button class="btn" id="saveWeights">Сохранить веса</button>
      </div>`;

    const w = state.user.crit_weights || { service: 0.25, seller: 0.25, product: 0.25, delivery: 0.25 };
    ["service", "seller", "product", "delivery"].forEach((k) => {
      const inp = $(`#w-${k}`, root);
      inp.value = w[k] != null ? w[k] : 0.25;
    });

    $("#saveWeights", root).onclick = async () => {
      const body = {
        service: parseFloat($("#w-service", root).value) || 0,
        seller: parseFloat($("#w-seller", root).value) || 0,
        product: parseFloat($("#w-product", root).value) || 0,
        delivery: parseFloat($("#w-delivery", root).value) || 0,
      };
      try {
        const res = await api("/users/me/weights", { method: "PUT", auth: true, body });
        state.user.crit_weights = res.crit_weights;
        toast("Веса сохранены", "ok");
      } catch (e) { toast(e.message, "err"); }
    };
  }

  function weightRow(key, label) {
    return `<label class="field"><span class="lbl">${label}</span>
      <input id="w-${key}" type="number" min="0" max="1" step="0.05" /></label>`;
  }

  // ---- Аутентификация ----
  function viewAuth(root) {
    root.innerHTML = `
      <div class="page-head"><div><h1>Вход и регистрация</h1>
      <p>Войдите, чтобы оставлять отзывы и комментарии</p></div></div>
      <div class="grid-2">
        <div class="card">
          <h2>Вход</h2>
          <label class="field"><span class="lbl">Email</span>
            <input id="li-email" value="user1@example.com" /></label>
          <label class="field"><span class="lbl">Пароль</span>
            <input id="li-pass" type="password" value="password123" /></label>
          <button class="btn" id="loginBtn">Войти</button>
          <p class="hint" style="margin-top:12px">Демо-аккаунт: user1@example.com / password123</p>
        </div>
        <div class="card">
          <h2>Регистрация</h2>
          <label class="field"><span class="lbl">Email</span>
            <input id="rg-email" placeholder="you@example.com" /></label>
          <label class="field"><span class="lbl">Имя</span>
            <input id="rg-name" placeholder="Ваше имя" /></label>
          <label class="field"><span class="lbl">Пароль (мин. 6 символов)</span>
            <input id="rg-pass" type="password" /></label>
          <button class="btn secondary" id="regBtn">Создать аккаунт</button>
        </div>
      </div>`;

    $("#loginBtn", root).onclick = async () => {
      try {
        const data = await api("/auth/login", {
          method: "POST",
          form: { username: $("#li-email", root).value, password: $("#li-pass", root).value },
        });
        setToken(data.access_token);
        await loadMe();
        syncNav();
        toast("Вход выполнен", "ok");
        location.hash = "#/search";
      } catch (e) { toast(e.message, "err"); }
    };

    $("#regBtn", root).onclick = async () => {
      try {
        await api("/auth/register", {
          method: "POST",
          body: {
            email: $("#rg-email", root).value,
            display_name: $("#rg-name", root).value,
            password: $("#rg-pass", root).value,
          },
        });
        toast("Аккаунт создан. Теперь войдите.", "ok");
      } catch (e) { toast(e.message, "err"); }
    };
  }

  // ============================================================
  //  РОУТЕР
  // ============================================================
  async function router() {
    const root = $("#app");
    const hash = location.hash || "#/search";
    const parts = hash.replace("#/", "").split("/");
    const route = parts[0] || "search";

    if (route === "logout") {
      setToken(null); state.user = null; syncNav();
      toast("Вы вышли из системы", "ok");
      location.hash = "#/search";
      return;
    }

    syncNav();

    switch (route) {
      case "search": viewSearch(root); break;
      case "review": await viewReview(root, parts[1]); break;
      case "new": viewNew(root); break;
      case "analytics": await viewAnalytics(root); break;
      case "profile": await viewProfile(root); break;
      case "auth": viewAuth(root); break;
      default: viewSearch(root);
    }
  }

  // ---------- Инициализация ----------
  async function init() {
    await loadMe();
    await loadRefs();
    syncNav();
    window.addEventListener("hashchange", router);
    router();
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", App.init);
