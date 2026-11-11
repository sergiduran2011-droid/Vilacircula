(() => {
  const TOKEN_KEY = 'vilacircula-api-token';
  const API_CONFIG = fetch('./api-config.json?v=3')
    .then(response => response.ok ? response.json() : {})
    .catch(() => ({}));

  async function apiUrl(path) {
    const config = await API_CONFIG;
    const origin = typeof config.apiBaseUrl === 'string' ? config.apiBaseUrl.replace(/\/+$/, '') : '';
    return `${origin ? `${origin}/api/v1` : './api/v1'}${path}`;
  }
  const status = document.createElement('div');
  status.className = 'api-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.textContent = 'Modo de demostración';
  document.querySelector('.topbar').after(status);
  const legalFooter = document.createElement('footer');
  legalFooter.className = 'legal-footer';
  legalFooter.innerHTML = '<div><strong>VilaCircula</strong><span>Projecte Talent a les Aules</span></div><nav aria-label="Informació legal"><a href="./legal.html#privacidad">Política de Privacitat i RGPD</a><a href="./legal.html#terminos">Termes d’ús i prevenció del frau</a><a href="./legal.html#galetes">Política de Galetes</a><button type="button" id="merchant-registration-open">Alta de comerços</button></nav>';
  document.body.append(legalFooter);
  document.querySelector('#merchant-registration-open').addEventListener('click', openMerchantRegistration);

  function openMerchantRegistration() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = '<section class="modal profile-modal merchant-registration" role="dialog" aria-modal="true" aria-labelledby="merchant-registration-title"><button class="icon-button modal-close" type="button" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">DIRECTORIO DE VILADECANS</span><h2 id="merchant-registration-title">Da de alta tu comercio.</h2><p>Prepara una solicitud para revisar la incorporación del establecimiento al directorio público.</p><form id="merchant-registration-form"><label for="merchant-public-name">Nombre del establecimiento</label><input id="merchant-public-name" name="name" maxlength="100" required><label for="merchant-public-logo">URL del logotipo</label><input id="merchant-public-logo" name="logo" type="url" maxlength="500" placeholder="https://…" required><label for="merchant-public-location">Ubicación que se mostrará</label><input id="merchant-public-location" name="location" maxlength="200" required><label for="merchant-contact-email">Correo de contacto</label><input id="merchant-contact-email" name="email" type="email" autocomplete="email" required><label class="legal-consent"><input name="display_consent" type="checkbox" required><span>Autorizo a VilaCircula a mostrar el nombre, logotipo y ubicación del establecimiento en el directorio público.</span></label><p class="profile-privacy">La solicitud se revisará antes de publicar el establecimiento. <a href="./legal.html#privacidad" target="_blank" rel="noopener">Política de Privacitat</a></p><button class="primary profile-submit" type="submit">Preparar solicitud</button><p class="profile-error" id="merchant-registration-status" role="status" aria-live="polite"></p></form></section>';
    const modal = overlay.querySelector('.merchant-registration');
    const close = () => overlay.remove();
    overlay.querySelector('.modal-close').addEventListener('click', close);
    overlay.addEventListener('click', event => { if (event.target === overlay) close(); });
    overlay.querySelector('#merchant-registration-form').addEventListener('submit', event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const subject = `Solicitud de alta de comercio: ${String(data.get('name')).trim()}`;
      const body = [
        `Establecimiento: ${String(data.get('name')).trim()}`,
        `Logotipo: ${String(data.get('logo')).trim()}`,
        `Ubicación pública: ${String(data.get('location')).trim()}`,
        `Correo de contacto: ${String(data.get('email')).trim()}`,
        'Consentimiento: autorizo mostrar el nombre, logotipo y ubicación en el directorio público.'
      ].join('\n');
      overlay.querySelector('#merchant-registration-status').textContent =
        'Se abrirá tu aplicación de correo. Envía el mensaje para completar la solicitud; la publicación requiere revisión.';
      window.location.href = `mailto:sergiduran2011@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    });
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    modal.querySelector('input').focus();
  }
  const style = document.createElement('link');
  style.rel = 'stylesheet';
  style.href = './api-client.css?v=30';
  document.head.append(style);
  const legalStyle = document.createElement('link');
  legalStyle.rel = 'stylesheet';
  legalStyle.href = './legal.css?v=1';
  document.head.append(legalStyle);
  const cashierStyle = document.createElement('link');
  cashierStyle.rel = 'stylesheet';
  cashierStyle.href = './cashier.css';
  document.head.append(cashierStyle);
  const cashierDashboardStyle = document.createElement('link');
  cashierDashboardStyle.rel = 'stylesheet';
  cashierDashboardStyle.href = './cashier-dashboard.css';
  document.head.append(cashierDashboardStyle);

  let token = localStorage.getItem(TOKEN_KEY);
  let profile = null;
  let stepActivityDate = null;
  let stepCount = 0;
  let stepGoal = 5000;
  let stepRewarded = false;
  let stepSensorActive = false;
  let stepSyncBusy = false;
  let stepSyncTimer = null;
  let stepMotionBaseline = null;
  let stepMotionArmed = true;
  let lastDetectedStepAt = 0;
  const updateBalance = window.update;
  const ECOPOINTS_PER_EURO = 30;
  window.update = function () {
    updateBalance();
    const balance = Number(document.querySelector('#balance').textContent);
    document.querySelector('#euros').textContent = (balance / ECOPOINTS_PER_EURO).toFixed(2).replace('.', ',');
  };
  window.update();
  let googleRegistrationConfig = { schools: [], student_registration_enabled: false };
  let liveApi = false;
  let rewards = [];
  let merchantCatalog = [];
  let googleSdkPromise;
  let pendingGoogleCredential = null;
  let deferredInstallPrompt = null;
  const ONBOARDING_KEY = 'vilacircula-onboarding-seen';
  const INSTALLED_KEY = 'vilacircula-installed';

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredInstallPrompt = event;
  });

  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    localStorage.setItem(INSTALLED_KEY, '1');
    const installButton = document.querySelector('#install');
    if (installButton) installButton.style.display = 'none';
    document.querySelectorAll('.install-app-prompt').forEach(card => {
      card.classList.add('installed');
      card.querySelector('.install-app-button').textContent = 'Aplicación instalada';
      card.querySelector('.install-app-button').disabled = true;
      card.querySelector('.install-app-description').textContent = 'VilaCircula ya está instalada en este dispositivo.';
    });
  });

  document.querySelector('#install')?.addEventListener('click', () => {
    deferredInstallPrompt = null;
  });

  function isAppInstalled() {
    return localStorage.getItem(INSTALLED_KEY) === '1'
      || window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }

  function installInstructions() {
    const userAgent = navigator.userAgent;
    const isIOS = /iPhone|iPad|iPod/.test(userAgent)
      || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    if (isIOS) {
      return [
        'Abre VilaCircula en Safari.',
        'Pulsa el botón Compartir.',
        'Elige «Añadir a pantalla de inicio» y confirma con «Añadir».'
      ];
    }
    if (/Macintosh/.test(userAgent) && /Safari/.test(userAgent) && !/Chrome|Chromium|CriOS/.test(userAgent)) {
      return [
        'Abre el menú «Archivo» de Safari.',
        'Elige «Añadir al Dock».',
        'Confirma el nombre y pulsa «Añadir».'
      ];
    }
    if (/Android/.test(userAgent)) {
      return [
        'Abre el menú del navegador (⋮).',
        'Elige «Instalar aplicación» o «Añadir a pantalla de inicio».',
        'Confirma para añadir VilaCircula a tu dispositivo.'
      ];
    }
    return [
      'Abre el menú de tu navegador o busca el icono de instalación en la barra de direcciones.',
      'Elige «Instalar VilaCircula» o «Añadir al escritorio».',
      'Confirma la instalación.'
    ];
  }

  function openInstallInstructions() {
    const overlay = document.createElement('div');
    overlay.id = 'install-help-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = '<section class="modal install-help-modal" role="dialog" aria-modal="true" aria-labelledby="install-help-title"><button class="icon-button modal-close" id="install-help-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">VILACIRCULA EN TU DISPOSITIVO</span><h2 id="install-help-title">Añádela a tu pantalla.</h2><p>Sigue estos pasos en el navegador que estás usando:</p><ol class="install-instructions"></ol><button class="primary install-help-done" id="install-help-done">Entendido</button></section>';
    const instructions = overlay.querySelector('.install-instructions');
    installInstructions().forEach(text => {
      const item = document.createElement('li');
      item.textContent = text;
      instructions.append(item);
    });
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    const close = () => overlay.remove();
    overlay.querySelector('#install-help-close').addEventListener('click', close);
    overlay.querySelector('#install-help-done').addEventListener('click', close);
    overlay.addEventListener('click', event => { if (event.target === overlay) close(); });
  }

  async function requestAppInstall() {
    if (!deferredInstallPrompt) {
      openInstallInstructions();
      return null;
    }
    const prompt = deferredInstallPrompt;
    deferredInstallPrompt = null;
    const installButton = document.querySelector('#install');
    if (installButton) installButton.style.display = 'none';
    try {
      await prompt.prompt();
      return (await prompt.userChoice).outcome;
    } catch (error) {
      console.error('No se pudo abrir el diálogo de instalación de VilaCircula.', error);
      openInstallInstructions();
      return null;
    }
  }

  function addInstallPrompt(container) {
    if (isAppInstalled()) return;
    const card = document.createElement('aside');
    card.className = 'install-app-prompt';
    card.innerHTML = '<span class="install-app-icon"><i data-lucide="smartphone"></i></span><div class="install-app-copy"><strong>Ten VilaCircula en tu dispositivo.</strong><small class="install-app-description">Añádela al escritorio o a la pantalla de inicio para abrirla como una aplicación.</small></div><button class="install-app-button" type="button">Añadir aplicación</button>';
    container.append(card);
    window.lucide?.createIcons();
    card.querySelector('.install-app-button').addEventListener('click', async () => {
      const outcome = await requestAppInstall();
      if (outcome === 'accepted') card.querySelector('.install-app-description').textContent = 'VilaCircula se está añadiendo a este dispositivo.';
      else if (outcome === 'dismissed') card.querySelector('.install-app-description').textContent = 'Puedes instalarla más tarde desde el menú del navegador.';
    });
  }

  async function registerServiceWorker() {
    if (!('serviceWorker' in navigator) || !window.isSecureContext) return;
    try {
      await navigator.serviceWorker.register('./sw.js', { scope: './' });
    } catch (error) {
      console.error('No se pudo registrar el service worker de VilaCircula.', error);
      setStatus('No se pudo preparar la instalación de la app. Recarga la página o prueba otro navegador.', 'error');
    }
  }

  function setButtonLoading(button, label = 'Procesando…') {
    if (!button) return;
    button.dataset.defaultLabel = button.textContent || '';
    button.disabled = true;
    button.textContent = label;
  }

  function resetButtonLoading(button) {
    if (!button) return;
    const original = button.dataset.defaultLabel || 'Continuar';
    button.disabled = false;
    button.textContent = original;
  }

  function getApiErrorMessage(error) {
    const message = typeof error?.message === 'string' ? error.message : String(error || '');
    if (/(qr|código|cupón).*(expir|caduc)|(expir|caduc).*(qr|código|cupón)/i.test(message)) {
      return 'El código QR ha caducado. Genera uno nuevo y vuelve a escanearlo.';
    }
    if (/Failed to fetch|NetworkError|fetch failed|Load failed|network request/i.test(message)) {
      return 'No hay conexión con VilaCircula. Comprueba tu conexión e inténtalo de nuevo.';
    }
    if (/401|Unauthorized/.test(message)) return 'La sesión no es válida o ha caducado. Vuelve a iniciar sesión.';
    if (/403|Forbidden/.test(message)) return 'No tienes permiso para hacer esta acción.';
    if (/404|Not Found/.test(message)) return 'No se ha encontrado la información solicitada.';
    if (/409|Conflict/.test(message)) return 'Ya existe ese registro o la operación ya se había realizado.';
    if (/422|Unprocessable/.test(message)) return 'Revisa los datos del formulario y vuelve a intentarlo.';
    if (/429|Too Many/.test(message)) return 'Demasiados intentos. Espera unos minutos antes de volver a probar.';
    if (/^[\w.]+Error:|Traceback|Exception|SQL|database|stack|undefined|null/i.test(message)) {
      return 'No se pudo completar la solicitud. Comprueba los datos e inténtalo de nuevo.';
    }
    return 'No se pudo completar la solicitud. Comprueba los datos e inténtalo de nuevo.';
  }

  async function request(path, options = {}) {
    return requestWithToken(path, options, token);
  }

  async function requestWithToken(path, options = {}, bearerToken = null) {
    const headers = new Headers(options.headers || {});
    if (bearerToken) headers.set('Authorization', `Bearer ${bearerToken}`);
    if (options.body) headers.set('Content-Type', 'application/json');
    let response;
    try {
      response = await fetch(await apiUrl(path), { ...options, headers });
    } catch (error) {
      if (error instanceof TypeError || !navigator.onLine) {
        throw new Error('No hay conexión con VilaCircula. Comprueba tu conexión e inténtalo de nuevo.', { cause: error });
      }
      throw error;
    }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Error del servidor (${response.status}).`);
    return payload;
  }

  function escapeHtml(value) {
    const node = document.createElement('span');
    node.textContent = String(value ?? '');
    return node.innerHTML;
  }

  function setStatus(message, mode = 'demo') {
    status.textContent = message;
    status.dataset.mode = mode;
  }

  function notifyUser(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body: message, icon: './icons/icon.svg' });
    }
    if (document.visibilityState === 'hidden' || !navigator.onLine) {
      setStatus(message, 'connected');
    }
  }

  async function enableNotifications() {
    if (!('Notification' in window)) return false;
    if (Notification.permission === 'granted') return true;
    if (Notification.permission === 'denied') return false;
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  function buildRewardSummary() {
    const total = rewards.reduce((sum, item) => sum + item.cost, 0);
    const nextGoal = Math.max(0, 80 - state.balance % 80);
    const summary = document.createElement('div');
    summary.className = 'reward-summary';
    summary.innerHTML = `
      <div class="reward-summary-head">
        <strong>Tu plan de recompensas</strong>
        <span class="eyebrow">ACTIVO</span>
      </div>
      <div class="reward-summary-grid">
        <div class="stat-pill"><small>Disponibles</small><strong>${state.balance}</strong></div>
        <div class="stat-pill"><small>Más cercano</small><strong>${rewards[0]?.cost || 0}</strong></div>
        <div class="stat-pill"><small>Siguiente meta</small><strong>${nextGoal}</strong></div>
      </div>
    `;
    return summary;
  }

  function renderAdminMetrics(report) {
    const summary = report.summary || {};
    const factors = report.conversion_factors || {};
    const cityImpact = report.city_impact || {};
    const metrics = [
      { label: 'Perfiles', value: summary.total_profiles || 0, detail: 'activos esta semana' },
      { label: 'Validaciones', value: summary.total_validations || 0, detail: 'total registradas' },
      { label: 'Éxitos', value: summary.successful_validations || 0, detail: 'cupones validados' },
      { label: 'Caja', value: summary.total_cashiers || 0, detail: 'usuarios de comercio' },
      { label: 'CO₂ evitado', value: `${Number(cityImpact.co2_avoided_kg || 0).toLocaleString(window.vilaLocale?.() || 'ca-ES')} kg`, detail: `${cityImpact.eco_purchases || 0} compras ECO verificadas` },
    ];
    return `
      <div class="admin-dashboard">
        <div class="admin-metric-grid">
          ${metrics.map(metric => `
            <div class="admin-metric">
              <small>${metric.label}</small>
              <strong>${metric.value}</strong>
              <span>${metric.detail}</span>
            </div>
          `).join('')}
        </div>
        <section class="conversion-factors">
          <strong>Factores de conversión</strong>
          <span>${Number(factors.steps_per_kg || 10000).toLocaleString(window.vilaLocale?.() || 'ca-ES')} pasos = 1 kg CO₂</span>
          <span>Compra ECO = ${Number(factors.eco_purchase_kg || 0.006) * 1000} g CO₂</span>
          <span>EcoRuta: ${Number(factors.eco_route_km_per_kg || 7.5).toLocaleString(window.vilaLocale?.() || 'ca-ES')} km = 1 kg CO₂</span>
        </section>
        <div class="admin-chart">
          <div class="reward-summary-head"><strong>Actividad reciente</strong><span class="eyebrow">${summary.production ? 'PROD' : 'DEMO'}</span></div>
          ${(report.recent_validations || []).slice(0, 5).map(item => `
            <div class="admin-row">
              <strong>${item.code}</strong>
              <small>${item.status}</small>
              <span>${new Date(item.validated_at).toLocaleDateString(window.vilaLocale?.() || 'ca-ES')}</span>
            </div>
          `).join('') || '<div class="admin-row"><strong>No hay validaciones todavía</strong><small>sin datos</small><span>—</span></div>'}
        </div>
      </div>
    `;
  }

  async function openAdminDashboard() {
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `
      <section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="admin-title">
        <button class="icon-button modal-close" id="admin-close" aria-label="Cerrar"><i data-lucide="x"></i></button>
        <span class="eyebrow">PANEL MUNICIPAL</span>
        <h2 id="admin-title">Dashboard de administración</h2>
        <p>Resumen operativo del impacto y la actividad de VilaCircula.</p>
        <div class="profile-modal">
          <div class="admin-actions"><button type="button" class="profile-local" id="admin-close-action">Volver</button></div>
          <div id="admin-results"><p class="profile-error">Cargando dashboard…</p></div>
        </div>
      </section>
    `;
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    const resultNode = overlay.querySelector('#admin-results');
    try {
      resultNode.innerHTML = renderAdminMetrics(await request('/admin/analytics'));
    } catch (error) {
      resultNode.innerHTML = `<p class="profile-error">${getApiErrorMessage(error)}</p>`;
    }
    overlay.querySelector('#admin-close').addEventListener('click', closeProfileDialog);
    overlay.querySelector('#admin-close-action').addEventListener('click', closeProfileDialog);
  }

  function setConnectionState(online) {
    if (!online) {
      setStatus('Sin conexión · puedes consultar lo guardado en este dispositivo.', 'error');
      return;
    }
    if (liveApi) setStatus('Conexión recuperada · sincronizando tu cuenta…', 'connected');
  }

  function openOnboarding() {
    if (localStorage.getItem(ONBOARDING_KEY)) return;
    const overlay = document.createElement('div');
    overlay.id = 'onboarding-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal onboarding-modal" role="dialog" aria-modal="true" aria-labelledby="onboarding-title"><button class="icon-button modal-close" id="onboarding-close" aria-label="Cerrar bienvenida"><i data-lucide="x"></i></button><span class="eyebrow">PRIMEROS PASOS</span><h2 id="onboarding-title">Empieza en VilaCircula.</h2><p>Tu cuenta ya está lista. En menos de un minuto puedes empezar a usar tus EcoPuntos.</p><div class="onboarding-steps"><div><b>1</b><span><strong>Explora</strong><small>Descubre comercios cercanos y sus iniciativas.</small></span></div><div><b>2</b><span><strong>Participa</strong><small>Enséñale tu EcoID al comercio.</small></span></div><div><b>3</b><span><strong>Disfruta</strong><small>Canjea tus puntos por recompensas locales.</small></span></div></div><button class="primary" id="onboarding-start"><i data-lucide="map-pin"></i>Ver comercios</button><button class="profile-local" id="onboarding-later">Ahora no</button></section>`;
    document.querySelector('#modal-root').append(overlay);
    addInstallPrompt(overlay.querySelector('.onboarding-modal'));
    window.lucide?.createIcons();
    const finish = () => {
      localStorage.setItem(ONBOARDING_KEY, '1');
      overlay.remove();
    };
    overlay.querySelector('#onboarding-close').addEventListener('click', finish);
    overlay.querySelector('#onboarding-later').addEventListener('click', finish);
    overlay.querySelector('#onboarding-start').addEventListener('click', () => {
      finish();
      document.querySelector('[data-screen="shops"]')?.click();
    });
    overlay.addEventListener('click', event => { if (event.target === overlay) finish(); });
    overlay.querySelector('#onboarding-start').focus();
  }

  function updateProfileUi(value) {
    profile = value;
    window.applyCitizenProfile(value.display_name, value.school, value.role);
  }

  function decorateMerchants(entries) {
    return entries.map(merchant => ({
      ...merchant,
      distance: merchant.latitude == null ? 'Sin ubicación' : 'Activa ubicación'
    }));
  }

  async function loadAccount() {
    const [dashboard, merchantData, rewardData, wallet] = await Promise.all([
      request('/dashboard'),
      request('/merchants'),
      request('/rewards'),
      request('/coupons')
    ]);
    merchantCatalog = merchantData.items;
    rewards = rewardData.items;
    window.setCitizenDashboard(dashboard);
    await loadTodaySteps();
    window.setCitizenMerchants(decorateMerchants(merchantData.items));
    window.setCitizenWallet(rewards, wallet.active, wallet.redeemed);
    const rewardSummary = buildRewardSummary();
    const existingRewardSummary = document.querySelector('.reward-summary');
    if (existingRewardSummary) existingRewardSummary.remove();
    document.querySelector('#screen-wallet .section-head')?.after(rewardSummary);
    setStatus('Perfil de este dispositivo · 150 puntos iniciales y ofertas de prueba. Comercios geolocalizados desde OpenStreetMap.', 'connected');
  }

  function closeProfileDialog() {
    document.querySelector('#profile-dialog')?.remove();
  }

  function completeGoogleLogin(result) {
    token = result.token;
    localStorage.setItem(TOKEN_KEY, token);
    liveApi = true;
    updateProfileUi(result.profile);
    return loadAccount().then(() => {
      document.body.classList.remove('auth-locked');
      closeProfileDialog();
      openOnboarding();
    });
  }

  function loadGoogleIdentitySdk() {
    if (window.google?.accounts?.id) return Promise.resolve();
    if (googleSdkPromise) return googleSdkPromise;
    googleSdkPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = resolve;
      script.onerror = () => reject(new Error('No se pudo cargar el acceso seguro de Google.'));
      document.head.append(script);
    });
    return googleSdkPromise;
  }

  function showGoogleAccountChoices(overlay, claims) {
    overlay.querySelector('#profile-title').textContent = 'Vincula tu perfil.';
    overlay.querySelector('#profile-description').textContent =
      `La cuenta ${claims.email} todavía no está vinculada. Usa tus credenciales actuales o crea un perfil nuevo.`;
    overlay.querySelector('#google-button').hidden = true;
    const choices = overlay.querySelector('#google-link-options');
    choices.hidden = false;
    choices.innerHTML = `<form id="google-link-form"><label for="link-username">Usuario actual de VilaCircula</label><input id="link-username" name="username" minlength="3" maxlength="24" autocomplete="username" required><label for="link-password">Contraseña actual</label><input id="link-password" name="password" type="password" autocomplete="current-password" required><button class="primary profile-submit" type="submit">Vincular mi perfil</button></form><button class="profile-local" id="google-create-profile">Crear un perfil nuevo</button><p class="profile-error" id="google-link-error" role="alert"></p>`;
    choices.querySelector('#google-link-form').addEventListener('submit', async event => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const submit = choices.querySelector('.profile-submit');
      const error = choices.querySelector('#google-link-error');
      setButtonLoading(submit, 'Vinculando…');
      error.textContent = '';
      try {
        const result = await request('/auth/google', {
          method: 'POST',
          body: JSON.stringify({
            credential: pendingGoogleCredential,
            username: String(form.get('username')).trim(),
            password: String(form.get('password'))
          })
        });
        await completeGoogleLogin(result);
      } catch (errorValue) {
        error.textContent = getApiErrorMessage(errorValue);
        resetButtonLoading(submit);
      }
    });
    choices.querySelector('#google-create-profile').addEventListener('click', () => {
      const schoolOptions = googleRegistrationConfig.schools
        .map(school => `<option value="${escapeHtml(school)}">${escapeHtml(school)}</option>`)
        .join('');
      choices.innerHTML = `<form id="google-create-form"><label for="google-display-name">Nombre o apodo</label><input id="google-display-name" name="display_name" maxlength="32" autocomplete="nickname" required><label for="google-birth-date">Fecha de nacimiento</label><input id="google-birth-date" name="birth_date" type="date" max="${new Date().toISOString().slice(0, 10)}" required><div id="google-student-fields" hidden><label for="google-school">Tu instituto</label><select id="google-school" name="school"><option value="">Selecciona tu instituto</option>${schoolOptions}</select><label for="google-school-code">Código exclusivo del centro</label><input id="google-school-code" name="school_code" autocomplete="off" maxlength="64"><small>Solicita el código a tu centro educativo.</small><label class="legal-consent"><input id="student-legal-consent" name="legal_consent" type="checkbox" required disabled><span>Soy mayor de 14 años o tengo el consentimiento de mis tutores/centro educativo para utilizar VilaCircula y acepto la <a href="./legal.html#privacidad" target="_blank" rel="noopener">Política de Privacidad</a>.</span></label></div><button class="primary profile-submit" type="submit">Crear cuenta con Google</button></form><button class="profile-local" id="google-link-existing">Vincular un perfil que ya tengo</button><p class="profile-error" id="google-link-error" role="alert"></p>`;
      choices.querySelector('#google-display-name').value = claims.display_name || '';
      const birthDate = choices.querySelector('#google-birth-date');
      const studentFields = choices.querySelector('#google-student-fields');
      const school = choices.querySelector('#google-school');
      const schoolCode = choices.querySelector('#google-school-code');
      const legalConsent = choices.querySelector('#student-legal-consent');
      const updateRegistrationFields = () => {
        const selectedDate = birthDate.value ? new Date(`${birthDate.value}T00:00:00`) : null;
        const today = new Date();
        const age = selectedDate
          ? today.getFullYear() - selectedDate.getFullYear() - (
            today.getMonth() < selectedDate.getMonth()
            || (today.getMonth() === selectedDate.getMonth() && today.getDate() < selectedDate.getDate()) ? 1 : 0
          )
          : null;
        const isStudent = age !== null && age < 18;
        studentFields.hidden = !isStudent;
        school.required = isStudent;
        schoolCode.required = isStudent;
        legalConsent.required = isStudent;
        legalConsent.disabled = !isStudent;
        school.disabled = isStudent && !googleRegistrationConfig.student_registration_enabled;
        schoolCode.disabled = isStudent && !googleRegistrationConfig.student_registration_enabled;
      };
      birthDate.addEventListener('change', updateRegistrationFields);
      choices.querySelector('#google-create-form').addEventListener('submit', async event => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        const submit = choices.querySelector('.profile-submit');
        const error = choices.querySelector('#google-link-error');
        setButtonLoading(submit, 'Creando cuenta…');
        error.textContent = '';
        try {
          const dateOfBirth = String(form.get('birth_date'));
          const selectedDate = new Date(`${dateOfBirth}T00:00:00`);
          const today = new Date();
          const age = today.getFullYear() - selectedDate.getFullYear() - (
            today.getMonth() < selectedDate.getMonth()
            || (today.getMonth() === selectedDate.getMonth() && today.getDate() < selectedDate.getDate()) ? 1 : 0
          );
          if (age < 18 && !googleRegistrationConfig.student_registration_enabled) {
            throw new Error('El registro de estudiantes todavía no está habilitado por su centro educativo.');
          }
          const result = await request('/auth/google', {
            method: 'POST',
            body: JSON.stringify({
              credential: pendingGoogleCredential,
              display_name: String(form.get('display_name')).trim(),
              birth_date: dateOfBirth,
              legal_consent: form.get('legal_consent') === 'on',
              ...(age < 18 ? { school: String(form.get('school')), school_code: String(form.get('school_code')).trim() } : {})
            })
          });
          await completeGoogleLogin(result);
        } catch (errorValue) {
          error.textContent = getApiErrorMessage(errorValue);
          resetButtonLoading(submit);
        }
      });
      choices.querySelector('#google-link-existing').addEventListener('click', () => showGoogleAccountChoices(overlay, claims));
    });
  }

  async function initializeGoogleButton(overlay, linkCurrentSession) {
    const error = overlay.querySelector('#google-auth-error');
    try {
      const config = await request('/auth/google/config');
      googleRegistrationConfig = config;
      if (!config.client_id) {
        error.textContent = 'El acceso con Google todavía no está configurado en el servidor.';
        return;
      }
      await loadGoogleIdentitySdk();
      window.google.accounts.id.initialize({
        client_id: config.client_id,
        callback: async response => {
          pendingGoogleCredential = response.credential;
          error.textContent = '';
          try {
            const result = await request(linkCurrentSession ? '/auth/google/link' : '/auth/google', {
              method: 'POST',
              body: JSON.stringify({ credential: pendingGoogleCredential })
            });
            if (result.link_required) showGoogleAccountChoices(overlay, result);
            else await completeGoogleLogin(result);
          } catch (errorValue) {
            error.textContent = getApiErrorMessage(errorValue);
          }
        }
      });
      window.google.accounts.id.renderButton(overlay.querySelector('#google-button'), {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        shape: 'rectangular',
        text: 'signin_with',
        locale: 'es',
        width: Math.min(360, overlay.querySelector('.profile-modal').clientWidth - 48)
      });
    } catch (errorValue) {
      error.textContent = getApiErrorMessage(errorValue);
    }
  }

  function openAuthDialog(linkCurrentSession = false, existingProfile = null) {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    const authGate = document.body.classList.contains('auth-locked');
    overlay.className = `modal-backdrop${authGate ? ' auth-gate' : ''}`;
    const description = linkCurrentSession
      ? `Vincula Google para conservar el perfil ${existingProfile?.display_name || ''} · ${existingProfile?.school || ''}.`
      : authGate
        ? 'Inicia sesión con Google para acceder a tu espacio y tus EcoPuntos.'
        : 'Usa tu cuenta de Google para continuar.';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title">${authGate ? '<div class="auth-brand"><span class="auth-mark"><img src="./icons/boot-mark.png" alt="" width="24" height="32"></span><strong>Vila<span>Circula</span></strong></div>' : ''}<span class="eyebrow">VILADECANS · PERFIL CIUDADANO</span><h2 id="profile-title">${linkCurrentSession ? 'Vincula tu cuenta.' : authGate ? 'Tu ciudad, en marcha.' : 'Entra en VilaCircula.'}</h2><p id="profile-description"></p><div class="google-button" id="google-button"></div><p class="profile-error" id="google-auth-error" role="alert"></p><div id="google-link-options" hidden></div></section>`;
    overlay.querySelector('#profile-description').textContent = description;
    document.querySelector('#modal-root').append(overlay);
    if (!linkCurrentSession) addInstallPrompt(overlay.querySelector('.profile-modal'));
    window.lucide?.createIcons();
    overlay.addEventListener('click', event => { if (event.target === overlay && token) closeProfileDialog(); });
    initializeGoogleButton(overlay, linkCurrentSession);
  }

  function openProfileDialog() {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    const adminAction = profile?.role === 'admin'
      ? '<button class="profile-action" id="open-admin-dashboard"><i data-lucide="shield-check"></i>Panel municipal</button>'
      : '';
    const profileAction = 'Editar nombre';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button class="icon-button modal-close" id="profile-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">PERFIL VILACIRCULA</span><h2 id="profile-title">Tu cuenta</h2><p>${profile?.display_name || ''} · ${profile?.username || 'Modo local'}</p><div class="profile-actions"><button class="profile-action" id="edit-citizen-profile"><i data-lucide="user-round-cog"></i>${profileAction}</button><button class="profile-action" id="edit-citizen-credentials"><i data-lucide="key-round"></i>Usuario y contraseña</button><button class="profile-action" id="open-cashier"><i data-lucide="store"></i>Zona de caja de comercio</button>${adminAction}<button class="profile-action danger" id="citizen-logout"><i data-lucide="log-out"></i>Cerrar sesión</button></div><p class="profile-error" id="profile-error" role="alert"></p></section>`;
    document.querySelector('#modal-root').append(overlay);
    window.vilaMountLanguageSelector?.();
    window.lucide?.createIcons();
    overlay.querySelector('#profile-close').addEventListener('click', closeProfileDialog);
    overlay.addEventListener('click', event => { if (event.target === overlay) closeProfileDialog(); });
    overlay.querySelector('#edit-citizen-profile').addEventListener('click', () => openEditCitizenProfile());
    overlay.querySelector('#edit-citizen-credentials').addEventListener('click', () => openCitizenCredentials());
    overlay.querySelector('#open-cashier').addEventListener('click', openCashierLogin);
    overlay.querySelector('#open-admin-dashboard')?.addEventListener('click', openAdminDashboard);
    overlay.querySelector('#citizen-logout').addEventListener('click', logoutCitizen);
  }

  function openEditCitizenProfile() {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button class="icon-button modal-close" id="profile-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">PERFIL CIUDADANO</span><h2 id="profile-title">Editar perfil</h2><form id="profile-form"><label for="citizen-name">Nombre o apodo</label><input id="citizen-name" name="display_name" maxlength="32" required><button class="primary profile-submit" type="submit">Guardar cambios</button><p class="profile-error" id="profile-error" role="alert"></p></form></section>`;
    document.querySelector('#modal-root').append(overlay);
    overlay.querySelector('#citizen-name').value = profile?.display_name || '';
    overlay.querySelector('#profile-close').addEventListener('click', openProfileDialog);
    overlay.querySelector('#profile-form').addEventListener('submit', async event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const submit = overlay.querySelector('.profile-submit');
      submit.disabled = true;
      try {
        const saved = await request('/profile', { method: 'PUT', body: JSON.stringify({ display_name: String(data.get('display_name')).trim() }) });
        updateProfileUi({ ...profile, ...saved });
        closeProfileDialog();
      } catch (error) {
        overlay.querySelector('#profile-error').textContent = getApiErrorMessage(error);
        submit.disabled = false;
      }
    });
  }

  function openCitizenCredentials() {
    closeProfileDialog();
    const needsSetup = Boolean(profile?.password_setup_required);
    const hasPassword = Boolean(profile?.has_password);
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button class="icon-button modal-close" id="profile-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">SEGURIDAD DE CUENTA</span><h2 id="profile-title">${needsSetup ? 'Protege tu cuenta.' : 'Cambiar credenciales'}</h2>${needsSetup ? '<p>Este perfil venía de la versión anterior. Añade usuario y contraseña antes de continuar.</p>' : ''}<form id="credentials-form"><label for="account-username">Nombre de usuario</label><input id="account-username" name="username" minlength="3" maxlength="24" pattern="[A-Za-z0-9._\\-]+" autocomplete="username" required><label for="current-password">Contraseña actual${hasPassword ? '' : ' (no configurada)'}</label><input id="current-password" name="current_password" type="password" autocomplete="current-password" ${hasPassword ? 'required' : ''}><label for="new-password">${hasPassword ? 'Nueva contraseña' : 'Crea una contraseña'}</label><input id="new-password" name="password" type="password" minlength="10" maxlength="128" autocomplete="new-password" required><button class="primary profile-submit" type="submit">Guardar credenciales</button><p class="profile-error" id="profile-error" role="alert"></p></form></section>`;
    document.querySelector('#modal-root').append(overlay);
    overlay.querySelector('#account-username').value = profile?.username || '';
    overlay.querySelector('#profile-close').addEventListener('click', openProfileDialog);
    overlay.querySelector('#credentials-form').addEventListener('submit', async event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const submit = overlay.querySelector('.profile-submit');
      submit.disabled = true;
      try {
        const result = await request('/account/credentials', { method: 'PUT', body: JSON.stringify({ username: String(data.get('username')).trim(), password: String(data.get('password')), current_password: String(data.get('current_password') || '') || null }) });
        token = result.token;
        localStorage.setItem(TOKEN_KEY, token);
        profile.username = result.username;
        profile.has_password = true;
        profile.password_setup_required = false;
        closeProfileDialog();
        setStatus('Credenciales actualizadas; las otras sesiones se han cerrado.', 'connected');
      } catch (error) {
        overlay.querySelector('#profile-error').textContent = getApiErrorMessage(error);
        submit.disabled = false;
      }
    });
  }

  async function logoutCitizen() {
    if (stepSensorActive) {
      window.removeEventListener('devicemotion', handleDeviceMotion);
      clearInterval(stepSyncTimer);
      stepSyncTimer = null;
      await syncStepCount();
      stepSensorActive = false;
    }
    try {
      await request('/auth/logout', { method: 'POST' });
    } catch {
      // A server-side expiry still clears the local session.
    }
    token = null;
    profile = null;
    liveApi = false;
    localStorage.removeItem(TOKEN_KEY);
    document.body.classList.add('auth-locked');
    closeProfileDialog();
    openAuthDialog();
    setStatus('Sesión cerrada.', 'demo');
  }

  async function openCashierLogin() {
    closeProfileDialog();
    const existingToken = sessionStorage.getItem('vilacircula-cashier-token');
    if (existingToken) {
      try {
        const cashier = await requestWithToken('/cashier/me', {}, existingToken);
        if (cashier.must_change_password) return openCashierPassword(existingToken, cashier);
        return openCashierConsole(existingToken, cashier);
      } catch {
        sessionStorage.removeItem('vilacircula-cashier-token');
      }
    }
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = '<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="cashier-login-title"><button class="icon-button modal-close" id="cashier-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">ACCESO DE COMERCIO</span><h2 id="cashier-login-title">Zona de caja</h2><p>Usa la cuenta que la persona responsable del comercio te haya asignado.</p><form id="cashier-login-form"><label for="cashier-username">Usuario de caja</label><input id="cashier-username" name="username" autocomplete="username" required><label for="cashier-password">Contraseña</label><input id="cashier-password" name="password" type="password" autocomplete="current-password" required><button class="primary profile-submit" type="submit">Entrar en caja</button><p class="profile-error" id="cashier-error" role="alert"></p></form></section>';
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    overlay.querySelector('#cashier-close').addEventListener('click', openProfileDialog);
    overlay.querySelector('#cashier-login-form').addEventListener('submit', async event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const submit = overlay.querySelector('.profile-submit');
      const errorNode = overlay.querySelector('#cashier-error');
      setButtonLoading(submit, 'Accediendo a caja…');
      errorNode.textContent = '';
      try {
        const result = await requestWithToken('/auth/cashier/login', {
          method: 'POST',
          body: JSON.stringify({ username: String(data.get('username')).trim(), password: String(data.get('password')) })
        }, null);
        sessionStorage.setItem('vilacircula-cashier-token', result.token);
        if (result.must_change_password) return openCashierPassword(result.token, { ...result.merchant, must_change_password: true });
        openCashierConsole(result.token, {
          merchant_id: result.merchant.id,
          merchant_name: result.merchant.name,
          merchant_is_demo: result.merchant.is_demo,
          must_change_password: result.must_change_password,
          username: result.username
        });
      } catch (error) {
        errorNode.textContent = getApiErrorMessage(error);
        resetButtonLoading(submit);
      }
    });
  }

  function openCashierPassword(cashierToken, cashier) {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    const forcedChange = Boolean(cashier.must_change_password);
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="cashier-password-title"><span class="eyebrow">${forcedChange ? 'PRIMER ACCESO' : 'SEGURIDAD DE CAJA'} · ${cashier.merchant_name || cashier.name}</span><h2 id="cashier-password-title">${forcedChange ? 'Cambia la clave inicial.' : 'Cambiar contraseña'}</h2><p>${forcedChange ? 'Por seguridad, debes reemplazarla antes de validar ningún cupón.' : 'Confirma tu clave actual para cambiarla.'}</p><form id="cashier-password-form">${forcedChange ? '' : '<label for="current-cashier-password">Contraseña actual</label><input id="current-cashier-password" name="current_password" type="password" autocomplete="current-password" required>'}<label for="new-cashier-password">Nueva contraseña</label><input id="new-cashier-password" name="password" type="password" minlength="10" maxlength="128" autocomplete="new-password" required><label for="confirm-cashier-password">Repite la contraseña</label><input id="confirm-cashier-password" name="confirmation" type="password" minlength="10" maxlength="128" autocomplete="new-password" required><button class="primary profile-submit" type="submit">Cambiar contraseña</button><p class="profile-error" id="cashier-password-error" role="alert"></p></form></section>`;
    document.querySelector('#modal-root').append(overlay);
    overlay.querySelector('#cashier-password-form').addEventListener('submit', async event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const password = String(data.get('password'));
      const submit = overlay.querySelector('.profile-submit');
      const errorNode = overlay.querySelector('#cashier-password-error');
      if (password !== data.get('confirmation')) {
        errorNode.textContent = 'Las contraseñas no coinciden.';
        return;
      }
      setButtonLoading(submit, 'Actualizando contraseña…');
      errorNode.textContent = '';
      try {
        const result = await requestWithToken('/cashier/password', { method: 'PUT', body: JSON.stringify({ password, current_password: String(data.get('current_password') || '') || null }) }, cashierToken);
        sessionStorage.setItem('vilacircula-cashier-token', result.token);
        const updated = await requestWithToken('/cashier/me', {}, result.token);
        openCashierConsole(result.token, updated);
      } catch (error) {
        errorNode.textContent = getApiErrorMessage(error);
        resetButtonLoading(submit);
      }
    });
  }

  let cashierStream;
  let cashierFrame;
  let cashierCanvas;
  let cashierScanning = false;

  async function startCashierScanner(cashierToken, root) {
    const statusNode = root.querySelector('#cashier-status');
    const video = root.querySelector('#cashier-video');
    const preview = root.querySelector('#cashier-preview');
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Este navegador no permite usar la cámara.');
      cashierStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
      video.srcObject = cashierStream;
      await video.play();
      preview.hidden = false;
      cashierCanvas = document.createElement('canvas');
      cashierScanning = true;
      statusNode.textContent = 'Apunta al QR de un cupón o EcoID VilaCircula.';
      let detector;
      if ('BarcodeDetector' in window) detector = new BarcodeDetector({ formats: ['qr_code'] });
      else if (!window.jsQR) await loadScript('https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js');
      const scan = async () => {
        if (!cashierScanning) return;
        try {
          let rawValue;
          if (detector) rawValue = (await detector.detect(video))[0]?.rawValue;
          else if (video.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
            cashierCanvas.width = video.videoWidth;
            cashierCanvas.height = video.videoHeight;
            const context = cashierCanvas.getContext('2d', { willReadFrequently: true });
            context.drawImage(video, 0, 0, cashierCanvas.width, cashierCanvas.height);
            rawValue = window.jsQR(context.getImageData(0, 0, cashierCanvas.width, cashierCanvas.height).data, cashierCanvas.width, cashierCanvas.height)?.data;
          }
          if (rawValue) {
            if (/^VCID-[A-F0-9]{32}$/i.test(rawValue.trim())) {
              const ecoPurchase = root.querySelector('#cashier-eco-purchase')?.checked === true;
              const result = await requestWithToken('/cashier/eco-id/scan', { method: 'POST', body: JSON.stringify({ code: rawValue.trim().toUpperCase(), eco_purchase: ecoPurchase }) }, cashierToken);
              await showCashierSuccess(root, { title: `+${result.points} EcoPuntos`, description: `${escapeHtml(result.display_name)} · ${escapeHtml(result.merchant)}`, kind: 'ecoid' }, cashierToken);
              return;
            }
            const code = rawValue.match(/VC-[A-Z0-9]{5,32}/i)?.[0]?.toUpperCase();
            if (!code) statusNode.textContent = 'El QR no es un cupón ni un EcoID VilaCircula.';
            else {
              const result = await requestWithToken('/cashier/coupons/redeem', { method: 'POST', body: JSON.stringify({ code }) }, cashierToken);
              await showCashierSuccess(root, { title: 'Cupón canjeado', description: `${escapeHtml(result.coupon.name)} · ${escapeHtml(result.merchant)}`, kind: 'coupon' }, cashierToken);
              return;
            }
          }
        } catch (error) {
          statusNode.textContent = getApiErrorMessage(error);
          if (error.message.includes('401')) cashierScanning = false;
        }
        if (cashierScanning) cashierFrame = requestAnimationFrame(scan);
      };
      scan();
    } catch (error) {
      statusNode.textContent = error.name === 'NotAllowedError'
        ? 'Permite el acceso a la cámara para escanear.'
        : getApiErrorMessage(error);
    }
  }

  function stopCashierScanner() {
    cashierScanning = false;
    if (cashierFrame) cancelAnimationFrame(cashierFrame);
    cashierStream?.getTracks().forEach(track => track.stop());
    cashierStream = null;
  }

  function cashierChart(data) {
    const counts = new Map(data.map(item => [item.date, item]));
    const days = Array.from({ length: 7 }, (_, index) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - index));
      const key = date.toISOString().slice(0, 10);
      return counts.get(key) || { date: key, coupons: 0, ecoids: 0 };
    });
    const max = Math.max(1, ...days.map(day => day.coupons + day.ecoids));
    return days.map(day => {
      const couponHeight = Math.max(0, Math.round(day.coupons / max * 100));
      const ecoHeight = Math.max(0, Math.round(day.ecoids / max * 100));
      const label = new Date(`${day.date}T12:00:00`).toLocaleDateString('es-ES', { weekday: 'short' });
      return `<div class="cashier-chart-day"><div class="cashier-chart-bars"><span class="cashier-bar-coupons" style="height:${couponHeight}%"></span><span class="cashier-bar-ecoid" style="height:${ecoHeight}%"></span></div><small>${label}</small></div>`;
    }).join('');
  }

  async function showCashierSuccess(root, feedback, cashierToken) {
    stopCashierScanner();
    if ('vibrate' in navigator) navigator.vibrate([90, 45, 120]);
    let dashboard = null;
    try {
      dashboard = await requestWithToken('/cashier/dashboard', {}, cashierToken);
    } catch {
      dashboard = { today: {}, week: {}, activity_by_day: [], recent_coupons: [], recent_ecoids: [] };
    }
    renderCashierWorkspace(root, dashboard, feedback);
  }

  function renderCashierWorkspace(root, dashboard, feedback = null) {
    const today = dashboard.today || {};
    const week = dashboard.week || {};
    const activities = [
      ...(dashboard.recent_coupons || []).map(item => ({ ...item, kind: 'coupon', title: item.status === 'success' ? 'Cupón canjeado' : 'Intento de canje', detail: item.code })),
      ...(dashboard.recent_ecoids || []).map(item => ({ ...item, kind: 'ecoid', title: 'EcoID validado', detail: '+10 EcoPuntos' }))
    ].sort((first, second) => second.validated_at || second.created_at ? Date.parse(second.validated_at || second.created_at) - Date.parse(first.validated_at || first.created_at) : 0).slice(0, 8);
    const merchantLabel = escapeHtml(dashboard.merchant || 'Comercio');
    root.innerHTML = `<header class="cashier-topbar"><a class="cashier-brand"><span class="cashier-brand-mark"><i data-lucide="leaf"></i></span><span><b>VilaCircula</b><small>Terminal de comercio</small></span></a><div class="cashier-top-actions"><span class="cashier-merchant"><i data-lucide="store"></i>${merchantLabel}</span><button class="icon-button" id="cashier-change-password" aria-label="Cambiar contraseña" title="Cambiar contraseña"><i data-lucide="key-round"></i></button><button class="icon-button" id="cashier-exit" aria-label="Salir de caja" title="Salir de caja"><i data-lucide="log-out"></i></button></div></header><main class="cashier-main"><section class="cashier-welcome"><div><span class="eyebrow">PANEL DE CAJA</span><h1>Hola, ${cashierName || 'equipo'}.</h1><p>Actividad y herramientas de ${merchantLabel}.</p></div><span class="cashier-live"><i></i> CONECTADO</span></section>${dashboard.is_demo ? '<p class="cashier-demo-note">Entorno de demostración</p>' : ''}<section class="cashier-metrics" aria-label="Resumen de hoy"><article class="cashier-metric"><span><i data-lucide="ticket-check"></i>Cupones canjeados</span><strong>${today.successful_coupons || 0}</strong><small>hoy · ${week.successful_coupons || 0} esta semana</small></article><article class="cashier-metric cashier-metric-points"><span><i data-lucide="scan-line"></i>EcoID validados</span><strong>${today.ecoid_scans || 0}</strong><small>hoy · ${week.ecoid_scans || 0} esta semana</small></article><article class="cashier-metric"><span><i data-lucide="activity"></i>Actividad total</span><strong>${(today.successful_coupons || 0) + (today.ecoid_scans || 0)}</strong><small>operaciones completadas hoy</small></article><article class="cashier-metric cashier-metric-alert"><span><i data-lucide="triangle-alert"></i>Incidencias</span><strong>${today.failed_coupons || 0}</strong><small>cupones rechazados hoy</small></article></section><section class="cashier-columns"><div class="cashier-main-column"><section class="cashier-scanner-panel"><div class="cashier-section-heading"><div><span class="eyebrow">VALIDACIÓN SEGURA</span><h2>Escanear cliente</h2><p>Lee un cupón para canjearlo o un EcoID para sumar puntos.</p></div><span class="cashier-scan-icon"><i data-lucide="scan-qr-code"></i></span></div><div class="cashier-scanner-preview" id="cashier-preview" hidden><video id="cashier-video" playsinline muted></video><span class="cashier-scan-frame"></span></div><div class="cashier-feedback ${feedback ? 'is-success' : ''}" id="cashier-feedback" role="status" aria-live="polite">${feedback ? `<i data-lucide="circle-check"></i><span><b>${feedback.title}</b><small>${feedback.description}</small></span>` : '<i data-lucide="scan-line"></i><span><b>Listo para escanear</b><small>El QR se valida con el servidor y solo puede usarse una vez.</small></span>'}</div><p class="cashier-scan-status" id="cashier-status">Cámara apagada. Pulsa para iniciar.</p>${dashboard.is_demo ? '' : '<label class="cashier-eco-purchase"><input id="cashier-eco-purchase" type="checkbox"><span>Compra ECO confirmada por el comercio</span></label>'}<div class="cashier-scan-actions"><button class="primary" id="cashier-start-scan"><i data-lucide="camera"></i>Escanear QR</button><button class="cashier-secondary" id="cashier-next-scan" ${feedback ? '' : 'hidden'}><i data-lucide="scan-line"></i>Escanear siguiente</button></div><div class="cashier-manual-entry"><label for="manual-coupon-code">Código manual</label><div class="row"><input id="manual-coupon-code" type="text" autocomplete="off" placeholder="VC-... o VCID-..." maxlength="40" /><button class="primary" type="button" id="manual-coupon-submit">Validar</button></div></div></section><section class="cashier-activity-panel"><div class="cashier-section-heading"><div><span class="eyebrow">REGISTRO DEL COMERCIO</span><h2>Actividad reciente</h2></div><button class="cashier-refresh" id="cashier-refresh" aria-label="Actualizar actividad" title="Actualizar"><i data-lucide="refresh-cw"></i></button></div>${activities.length ? `<div class="cashier-activity-list">${activities.map(item => `<article class="cashier-activity-row"><span class="cashier-activity-icon ${item.kind}"><i data-lucide="${item.kind === 'ecoid' ? 'scan-line' : item.status === 'success' ? 'ticket-check' : 'circle-alert'}"></i></span><span><b>${item.title}</b><small>${item.detail}</small></span><time>${new Date(item.validated_at || item.created_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}</time></article>`).join('')}</div>` : '<p class="cashier-empty">Aún no hay operaciones registradas.</p>'}</section></div><aside class="cashier-side-column"><section class="cashier-chart-panel"><div class="cashier-section-heading"><div><span class="eyebrow">ÚLTIMOS 7 DÍAS</span><h2>Ritmo del comercio</h2></div></div><div class="cashier-chart-legend"><span><i class="coupon-key"></i>Cupones</span><span><i class="ecoid-key"></i>EcoID</span></div><div class="cashier-chart" role="img" aria-label="Operaciones diarias por tipo">${cashierChart(dashboard.activity_by_day || [])}</div><div class="cashier-chart-caption">Cada barra representa operaciones validadas en el día.</div></section><section class="cashier-tip"><span class="cashier-tip-icon"><i data-lucide="shield-check"></i></span><div><b>Validación protegida</b><p>Los cupones y EcoID caducan o se consumen al validarse. Los puntos se asignan desde el servidor a la cuenta correcta.</p></div></section></aside></section></main>`;
    const cashierLogo = root.querySelector('.cashier-brand-mark');
    const cashierLogoImage = document.createElement('img');
    cashierLogoImage.src = './icons/boot-mark.png';
    cashierLogoImage.alt = '';
    cashierLogoImage.width = 24;
    cashierLogoImage.height = 32;
    cashierLogo?.replaceChildren(cashierLogoImage);
    if (feedback) root.querySelector('#cashier-feedback')?.classList.add('is-success');
    window.lucide?.createIcons();
    const addRewardButton = document.createElement('button');
    addRewardButton.type = 'button';
    addRewardButton.id = 'cashier-add-reward';
    addRewardButton.className = 'cashier-add-reward';
    addRewardButton.setAttribute('aria-label', 'Añadir cupón');
    addRewardButton.innerHTML = '<i data-lucide="plus"></i><span>Añadir cupón</span>';
    root.querySelector('.cashier-top-actions')?.insertBefore(
      addRewardButton,
      root.querySelector('#cashier-change-password')
    );
    addRewardButton.addEventListener('click', () => {
      const offerPanel = root.querySelector('#cashier-rewards-panel');
      offerPanel?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      offerPanel?.querySelector('input[name="name"]')?.focus({ preventScroll: true });
    });
    window.lucide?.createIcons();
    root.querySelector('#cashier-start-scan').addEventListener('click', () => startCashierScanner(cashierToken, root));
    root.querySelector('#cashier-next-scan')?.addEventListener('click', () => startCashierScanner(cashierToken, root));
    root.querySelector('#cashier-change-password').addEventListener('click', () => {
      stopCashierScanner();
      root.remove();
      openCashierPassword(cashierToken, cashier);
    });
    root.querySelector('#cashier-exit').addEventListener('click', () => {
      stopCashierScanner();
      root.remove();
      openProfileDialog();
    });
    root.querySelector('#cashier-refresh').addEventListener('click', refreshCashierDashboard);
    root.querySelector('#manual-coupon-submit').addEventListener('click', submitManualCashierCode);
    root.querySelector('#manual-coupon-code').addEventListener('keydown', event => {
      if (event.key === 'Enter') submitManualCashierCode();
    });
    renderCashierOffers(root);
  }

  function renderCashierOffers(root) {
    if (!document.querySelector('link[data-cashier-rewards-styles]')) {
      const stylesheet = document.createElement('link');
      stylesheet.rel = 'stylesheet';
      stylesheet.href = './cashier-rewards.css?v=3';
      stylesheet.dataset.cashierRewardsStyles = '';
      document.head.append(stylesheet);
    }
    const panel = document.createElement('section');
    panel.id = 'cashier-rewards-panel';
    panel.className = 'cashier-rewards-panel';
    panel.innerHTML = '<div class="cashier-section-heading"><div><span class="eyebrow">CATÁLOGO CIUDADANO</span><h2>Ofertas y cupones</h2><p>Las ofertas activas se publican en el catálogo de la app.</p></div><span class="cashier-offer-icon"><i data-lucide="ticket-percent"></i></span></div><form id="cashier-reward-form" class="cashier-reward-form"><label>Qué recibe la persona<input name="name" maxlength="100" required placeholder="Ej.: Café y pieza de bollería"></label><label>Coste en EcoPuntos<input name="cost" type="number" min="1" max="100000" step="1" required placeholder="Ej.: 45"></label><label>Descripción breve<textarea name="description" maxlength="280" minlength="5" required rows="3" placeholder="Indica condiciones o detalles de la oferta"></textarea></label><label class="cashier-student-featured"><input name="student_featured" type="checkbox"><span>Mostrar en el apartado para estudiantes<small>Solo hará que aparezca en ese apartado; no limita quién puede verla o canjearla.</small></span></label><button class="cashier-offer-submit" type="submit"><i data-lucide="plus"></i>Publicar oferta</button><p class="cashier-offer-status" id="cashier-reward-status" role="status" aria-live="polite"></p></form><div class="cashier-offer-list" id="cashier-reward-list"><p class="cashier-empty">Cargando tus ofertas…</p></div>';
    root.querySelector('.cashier-scanner-panel')?.after(panel);
    window.lucide?.createIcons();

    const status = panel.querySelector('#cashier-reward-status');
    const list = panel.querySelector('#cashier-reward-list');
    const loadOffers = async () => {
      try {
        const result = await requestWithToken('/cashier/rewards', {}, cashierToken);
        list.innerHTML = result.items.length
          ? result.items.map(item => `<article class="cashier-offer-row"><div><b>${escapeHtml(item.name)}</b><p>${escapeHtml(item.description)}</p><small>${escapeHtml(item.cost)} EcoPuntos · ${item.active ? 'Publicada' : 'Pausada'}${item.student_featured ? ' · Apartado para estudiantes' : ''}</small></div><button type="button" class="cashier-offer-toggle" data-reward-id="${escapeHtml(item.id)}" data-active="${item.active}" aria-label="${item.active ? 'Pausar' : 'Publicar'} ${escapeHtml(item.name)}">${item.active ? 'Pausar' : 'Publicar'}</button></article>`).join('')
          : '<p class="cashier-empty">Aún no has publicado ofertas.</p>';
        list.querySelectorAll('.cashier-offer-toggle').forEach(button => {
          button.addEventListener('click', async () => {
            button.disabled = true;
            status.textContent = '';
            try {
              await requestWithToken(`/cashier/rewards/${encodeURIComponent(button.dataset.rewardId)}`, {
                method: 'PATCH',
                body: JSON.stringify({ active: button.dataset.active !== 'true' })
              }, cashierToken);
              await loadOffers();
            } catch (error) {
              status.textContent = getApiErrorMessage(error);
              button.disabled = false;
            }
          });
        });
      } catch (error) {
        list.innerHTML = `<p class="cashier-empty">${escapeHtml(getApiErrorMessage(error))}</p>`;
      }
    };

    panel.querySelector('#cashier-reward-form').addEventListener('submit', async event => {
      event.preventDefault();
      const form = event.currentTarget;
      const submit = form.querySelector('button[type="submit"]');
      const values = new FormData(form);
      submit.disabled = true;
      status.textContent = 'Publicando oferta…';
      try {
        await requestWithToken('/cashier/rewards', {
          method: 'POST',
          body: JSON.stringify({
            name: String(values.get('name')).trim(),
            cost: Number(values.get('cost')),
            description: String(values.get('description')).trim(),
            student_featured: values.get('student_featured') === 'on'
          })
        }, cashierToken);
        form.reset();
        status.textContent = 'Oferta publicada y visible en el catálogo.';
        await loadOffers();
      } catch (error) {
        status.textContent = getApiErrorMessage(error);
      } finally {
        submit.disabled = false;
      }
    });
    loadOffers();
  }

  let cashierToken;
  let cashier;
  let cashierName;
  let cashierRoot;

  async function refreshCashierDashboard() {
    try {
      const dashboard = await requestWithToken('/cashier/dashboard', {}, cashierToken);
      renderCashierWorkspace(cashierRoot, dashboard);
    } catch (error) {
      const statusNode = cashierRoot?.querySelector('#cashier-status');
      if (statusNode) statusNode.textContent = getApiErrorMessage(error);
    }
  }

  async function submitManualCashierCode() {
    const codeInput = cashierRoot.querySelector('#manual-coupon-code');
    const code = codeInput.value.trim().toUpperCase();
    const statusNode = cashierRoot.querySelector('#cashier-status');
    if (!/^VC-[A-Z0-9]{5,32}$/.test(code) && !/^VCID-[A-F0-9]{32}$/.test(code)) {
      statusNode.textContent = 'Introduce un cupón VC-… o un EcoID VCID-… válido.';
      return;
    }
    try {
      if (code.startsWith('VCID-')) {
        const ecoPurchase = cashierRoot.querySelector('#cashier-eco-purchase')?.checked === true;
        const result = await requestWithToken('/cashier/eco-id/scan', { method: 'POST', body: JSON.stringify({ code, eco_purchase: ecoPurchase }) }, cashierToken);
        await showCashierSuccess(cashierRoot, { title: `+${result.points} EcoPuntos`, description: `${escapeHtml(result.display_name)} · ${escapeHtml(result.merchant)}`, kind: 'ecoid' }, cashierToken);
      } else {
        const result = await requestWithToken('/cashier/coupons/redeem', { method: 'POST', body: JSON.stringify({ code }) }, cashierToken);
        await showCashierSuccess(cashierRoot, { title: 'Cupón canjeado', description: `${escapeHtml(result.coupon.name)} · ${escapeHtml(result.merchant)}`, kind: 'coupon' }, cashierToken);
        notifyUser('Cupón canjeado', `${result.coupon.name} se ha validado correctamente.`);
      }
    } catch (error) {
      statusNode.textContent = getApiErrorMessage(error);
    }
  }

  async function openCashierConsole(cashierTokenValue, cashierValue) {
    closeProfileDialog();
    cashierToken = cashierTokenValue;
    cashier = cashierValue;
    cashierName = escapeHtml(cashierValue.username || cashierValue.merchant_name || cashierValue.name);
    cashierRoot?.remove();
    cashierRoot = document.createElement('div');
    cashierRoot.id = 'cashier-workspace';
    cashierRoot.className = 'cashier-workspace';
    document.body.append(cashierRoot);
    cashierRoot.innerHTML = '<div class="cashier-loading"><span></span><b>Cargando actividad de caja…</b></div>';
    try {
      const dashboard = await requestWithToken('/cashier/dashboard', {}, cashierToken);
      renderCashierWorkspace(cashierRoot, dashboard);
    } catch (error) {
      cashierRoot.innerHTML = `<div class="cashier-loading cashier-load-error"><b>No se pudo abrir el panel</b><p>${getApiErrorMessage(error)}</p><button class="primary" id="cashier-load-back">Volver</button></div>`;
      cashierRoot.querySelector('#cashier-load-back').addEventListener('click', () => { cashierRoot.remove(); openProfileDialog(); });
    }
  }

  let liveEcoIdTimer;
  let liveEcoIdPollTimer;
  let liveEcoIdRetryTimer;
  let liveEcoIdStreamController;
  let liveEcoIdVisibilityHandler;
  let liveEcoIdOnlineHandler;
  let liveEcoIdOfflineHandler;

  function closeLiveEcoId() {
    clearInterval(liveEcoIdTimer);
    clearInterval(liveEcoIdPollTimer);
    clearTimeout(liveEcoIdRetryTimer);
    liveEcoIdStreamController?.abort();
    liveEcoIdStreamController = null;
    if (liveEcoIdVisibilityHandler) {
      document.removeEventListener('visibilitychange', liveEcoIdVisibilityHandler);
      liveEcoIdVisibilityHandler = null;
    }
    if (liveEcoIdOnlineHandler) {
      window.removeEventListener('online', liveEcoIdOnlineHandler);
      liveEcoIdOnlineHandler = null;
    }
    if (liveEcoIdOfflineHandler) {
      window.removeEventListener('offline', liveEcoIdOfflineHandler);
      liveEcoIdOfflineHandler = null;
    }
    document.querySelector('#live-ecoid-dialog')?.remove();
  }

  async function openLiveEcoId() {
    closeLiveEcoId();
    const overlay = document.createElement('div');
    overlay.id = 'live-ecoid-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = '<section class="modal live-ecoid-modal" role="dialog" aria-modal="true" aria-labelledby="live-ecoid-title"><button class="icon-button modal-close" id="live-ecoid-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">IDENTIFICACIÓN · CAJA</span><h2 id="live-ecoid-title">Tu EcoID</h2><p>El cajero lo escanea para añadir 10 EcoPuntos a tu cuenta. Cada código solo sirve una vez.</p><div class="coupon-large-qr" id="live-ecoid-qr"></div><strong class="live-ecoid-countdown" id="live-ecoid-countdown">Preparando código…</strong><small class="live-ecoid-code" id="live-ecoid-code"></small><p class="live-ecoid-status" id="live-ecoid-status" role="status" aria-live="polite">Conectando para confirmar el escaneo…</p><p class="profile-error" id="live-ecoid-error" role="alert" aria-live="assertive"></p></section>';
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    overlay.querySelector('#live-ecoid-close').addEventListener('click', closeLiveEcoId);
    overlay.addEventListener('click', event => { if (event.target === overlay) closeLiveEcoId(); });
    const qrNode = overlay.querySelector('#live-ecoid-qr');
    const countdown = overlay.querySelector('#live-ecoid-countdown');
    const statusNode = overlay.querySelector('#live-ecoid-status');
    const errorNode = overlay.querySelector('#live-ecoid-error');
    let expiresAt = 0;
    let issuing = false;
    let pollInProgress = false;
    let streamConnecting = false;
    let streamConnected = false;
    let scanConfirmed = false;
    let codeExpired = false;
    let retryDelay = 1000;
    let codeIssueRetryDelay = 1000;

    const setConnectionStatus = (message, mode = 'waiting') => {
      statusNode.textContent = message;
      statusNode.dataset.mode = mode;
    };

    const stopMonitoring = () => {
      clearInterval(liveEcoIdPollTimer);
      clearTimeout(liveEcoIdRetryTimer);
      liveEcoIdStreamController?.abort();
      liveEcoIdStreamController = null;
      streamConnected = false;
    };

    const confirmScan = () => {
      if (scanConfirmed || !overlay.isConnected) return;
      scanConfirmed = true;
      clearInterval(liveEcoIdTimer);
      stopMonitoring();
      qrNode.replaceChildren();
      countdown.textContent = '¡EcoID escaneado correctamente!';
      overlay.querySelector('#live-ecoid-code').textContent = '';
      errorNode.textContent = '';
      setConnectionStatus('Se han añadido 10 EcoPuntos a tu cuenta.', 'success');
      if ('vibrate' in navigator) navigator.vibrate([80, 40, 100]);
      notifyUser('EcoID escaneado correctamente', 'Se han añadido 10 EcoPuntos a tu cuenta.');
      refreshWallet().catch(error => {
        console.error('No se pudo actualizar el saldo después de validar el EcoID.', error);
        setConnectionStatus('El escaneo se confirmó, pero no se pudo actualizar el saldo. Recarga la app para ver los puntos.', 'error');
      });
    };

    const handleEcoIdStatus = payload => {
      if (payload.scanned) {
        confirmScan();
      } else if (payload.expired) {
        codeExpired = true;
        setConnectionStatus('El código ha caducado; preparando otro…');
        expiresAt = Date.now();
      }
    };

    const issueCode = async () => {
      if (issuing || scanConfirmed) return;
      issuing = true;
      stopMonitoring();
      qrNode.replaceChildren();
      overlay.querySelector('#live-ecoid-code').textContent = '';
      setConnectionStatus('Generando un código seguro…');
      try {
        const issued = await request('/eco-id', { method: 'POST' });
        if (!overlay.isConnected) return;
        if (window.QRCode) new QRCode(qrNode, { text: issued.code, width: 184, height: 184, colorDark: '#19281f', colorLight: '#fff', correctLevel: QRCode.CorrectLevel.M });
        else qrNode.textContent = issued.code;
        overlay.querySelector('#live-ecoid-code').textContent = issued.code;
        expiresAt = Date.parse(issued.expires_at);
        codeExpired = false;
        codeIssueRetryDelay = 1000;
        errorNode.textContent = '';
        setConnectionStatus('Esperando a que la caja escanee tu código…');
        startMonitoring();
      } catch (error) {
        errorNode.textContent = getApiErrorMessage(error);
        setConnectionStatus('No se pudo generar el código. Se volverá a intentar automáticamente.', 'error');
        expiresAt = Date.now() + codeIssueRetryDelay;
        codeIssueRetryDelay = Math.min(codeIssueRetryDelay * 2, 15000);
      } finally {
        issuing = false;
      }
    };

    const checkScanStatus = async (force = false) => {
      const code = overlay.querySelector('#live-ecoid-code').textContent;
      if (pollInProgress || scanConfirmed || (streamConnected && !force) || !code || !overlay.isConnected || !navigator.onLine) return;
      pollInProgress = true;
      try {
        const result = await request(`/eco-id/${encodeURIComponent(code)}/status`);
        handleEcoIdStatus(result);
        if (!result.scanned && !result.expired && !streamConnected) {
          setConnectionStatus('Reconectando en tiempo real; comprobando el escaneo automáticamente…', 'reconnecting');
        }
      } catch (error) {
        if (!overlay.isConnected) return;
        if (/Inicia sesión|sesión ha caducado|Vincula una cuenta/.test(error.message)) {
          clearInterval(liveEcoIdTimer);
          stopMonitoring();
          errorNode.textContent = 'Tu sesión ha caducado. Cierra este aviso e inicia sesión de nuevo.';
          setConnectionStatus('No se puede confirmar el escaneo sin una sesión válida.', 'error');
          return;
        }
        setConnectionStatus('Sin conexión con el servidor; reintentando automáticamente…', 'error');
      } finally {
        pollInProgress = false;
      }
    };

    const consumeScanEvents = async (code, controller) => {
      const response = await fetch(await apiUrl(`/eco-id/${encodeURIComponent(code)}/events`), {
        headers: { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
        signal: controller.signal
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const error = new Error(payload.detail || `Error del servidor (${response.status}).`);
        error.status = response.status;
        throw error;
      }
      if (!response.body) throw new Error('El navegador no permite recibir eventos en tiempo real.');
      streamConnected = true;
      retryDelay = 1000;
      errorNode.textContent = '';
      setConnectionStatus('Conexión activa · esperando el escaneo de caja…', 'connected');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        while (!controller.signal.aborted) {
          const { value, done } = await reader.read();
          if (done) return;
          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split(/\r?\n\r?\n/);
          buffer = blocks.pop() || '';
          for (const block of blocks) {
            const data = block.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n');
            if (data) handleEcoIdStatus(JSON.parse(data));
            if (scanConfirmed || codeExpired || !overlay.isConnected) return;
          }
        }
      } finally {
        reader.releaseLock();
      }
    };

    const scheduleStreamReconnect = delay => {
      clearTimeout(liveEcoIdRetryTimer);
      liveEcoIdRetryTimer = setTimeout(() => {
        if (streamConnecting) scheduleStreamReconnect(250);
        else connectToScanEvents();
      }, delay);
    };

    const connectToScanEvents = async () => {
      const code = overlay.querySelector('#live-ecoid-code').textContent;
      if (streamConnecting || scanConfirmed || !code || !overlay.isConnected || !navigator.onLine) return;
      streamConnecting = true;
      const controller = new AbortController();
      liveEcoIdStreamController = controller;
      try {
        await consumeScanEvents(code, controller);
        if (codeExpired && overlay.isConnected && !scanConfirmed) {
          liveEcoIdRetryTimer = setTimeout(issueCode, 0);
          return;
        }
        if (!controller.signal.aborted && !scanConfirmed && overlay.isConnected) throw new Error('La conexión de confirmación se cerró.');
      } catch (error) {
        if (controller.signal.aborted || !overlay.isConnected || scanConfirmed) return;
        if (codeExpired) {
          liveEcoIdRetryTimer = setTimeout(issueCode, 0);
          return;
        }
        if (/Inicia sesión|sesión ha caducado|Vincula una cuenta/.test(error.message)) {
          clearInterval(liveEcoIdTimer);
          stopMonitoring();
          errorNode.textContent = 'Tu sesión ha caducado. Cierra este aviso e inicia sesión de nuevo.';
          setConnectionStatus('No se puede confirmar el escaneo sin una sesión válida.', 'error');
          return;
        }
        streamConnected = false;
        setConnectionStatus('Conexión en tiempo real interrumpida; reintentando y comprobando el estado…', 'reconnecting');
        if (!liveEcoIdPollTimer) liveEcoIdPollTimer = setInterval(checkScanStatus, 3000);
        scheduleStreamReconnect(retryDelay);
        retryDelay = Math.min(retryDelay * 2, 15000);
      } finally {
        if (liveEcoIdStreamController === controller) liveEcoIdStreamController = null;
        streamConnecting = false;
      }
    };

    const startMonitoring = () => {
      liveEcoIdPollTimer = setInterval(checkScanStatus, 3000);
      connectToScanEvents();
    };

    await issueCode();
    if (!overlay.isConnected) return;
    liveEcoIdTimer = setInterval(() => {
      const seconds = Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000));
      countdown.textContent = seconds ? `Se renueva en 00:${String(seconds).padStart(2, '0')}` : 'Renovando código…';
      if (seconds === 0 && !issuing && !streamConnecting) issueCode();
    }, 1000);
    liveEcoIdVisibilityHandler = () => {
      if (document.visibilityState === 'visible' && overlay.isConnected && !scanConfirmed) {
        liveEcoIdStreamController?.abort();
        streamConnected = false;
        checkScanStatus(true);
        scheduleStreamReconnect(250);
      }
    };
    document.addEventListener('visibilitychange', liveEcoIdVisibilityHandler);
    liveEcoIdOnlineHandler = () => {
      setConnectionStatus('Conexión recuperada; comprobando el código…', 'reconnecting');
      checkScanStatus(true);
      liveEcoIdStreamController?.abort();
      streamConnected = false;
      scheduleStreamReconnect(250);
    };
    liveEcoIdOfflineHandler = () => {
      setConnectionStatus('Sin conexión a internet. Se reanudará la confirmación al recuperar la conexión.', 'error');
      liveEcoIdStreamController?.abort();
      streamConnected = false;
    };
    window.addEventListener('online', liveEcoIdOnlineHandler);
    window.addEventListener('offline', liveEcoIdOfflineHandler);
  }

  async function refreshWallet() {
    const [dashboard, wallet] = await Promise.all([request('/dashboard'), request('/coupons')]);
    window.setCitizenDashboard(dashboard);
    window.setCitizenWallet(rewards, wallet.active, wallet.redeemed);
  }

  window.refreshCitizenWallet = refreshWallet;
  window.apiCouponStatus = async code => {
    const wallet = await request('/coupons');
    return wallet.redeemed.some(coupon => coupon.code === code);
  };

  window.apiCouponRedeem = async code => {
    try {
      const result = await request('/coupons/redeem', { method: 'POST', body: JSON.stringify({ code }) });
      const couponModal = document.querySelector('#coupon-modal .coupon-modal');
      if (couponModal) {
        const success = document.createElement('div');
        success.className = 'coupon-success';
        success.setAttribute('role', 'status');
        success.innerHTML = `<span class="coupon-success-mark"><i data-lucide="check"></i></span><strong>Cupón canjeado</strong><small>${escapeHtml(result.coupon?.name || 'Tu cupón')} se ha validado correctamente.</small>`;
        couponModal.append(success);
        window.lucide?.createIcons();
        await new Promise(resolve => setTimeout(resolve, 1250));
      }
      await refreshWallet();
      window.closeCitizenCouponModal();
      setStatus(result.is_demo ? 'Canje de prueba registrado en el servidor.' : 'Cupón validado por el servidor.', result.is_demo ? 'demo' : 'connected');
      if ('vibrate' in navigator) navigator.vibrate([70, 35, 70]);
      return true;
    } catch (error) {
      const scannerStatus = document.querySelector('#scanner-status');
      const friendly = getApiErrorMessage(error);
      if (scannerStatus) scannerStatus.textContent = friendly;
      else setStatus(friendly, 'error');
      return false;
    }
  };

  function renderStepCounter() {
    const count = document.querySelector('#step-count');
    const goal = document.querySelector('#step-goal');
    const progress = document.querySelector('#step-progress');
    const statusNode = document.querySelector('#step-counter-status');
    const rewardLabel = document.querySelector('#step-reward-label');
    const button = document.querySelector('#start-step-counter');
    if (count) count.textContent = `${stepCount.toLocaleString(window.vilaLocale?.() || 'ca-ES')} pasos`;
    if (goal) goal.textContent = `de ${stepGoal.toLocaleString(window.vilaLocale?.() || 'ca-ES')}`;
    if (progress) progress.style.width = `${Math.min(100, stepCount / stepGoal * 100)}%`;
    if (rewardLabel) rewardLabel.textContent = stepRewarded ? '✓ +30 pts conseguidos' : '+30 pts al alcanzar meta';
    if (button) button.textContent = stepSensorActive ? 'Pausar contador' : 'Activar contador de pasos';
    if (statusNode && !statusNode.dataset.error) {
      statusNode.textContent = stepRewarded
        ? '¡Meta diaria alcanzada! Tus 30 EcoPunts ya están en el saldo.'
        : stepSensorActive
          ? 'Contador activo. Mantén VilaCircula abierta para registrar tus pasos.'
          : 'Estimación con el acelerómetro mientras la app está abierta.';
    }
  }

  async function loadTodaySteps() {
    const result = await request('/steps/today');
    if (stepActivityDate !== result.activity_date) {
      stepCount = result.steps;
      stepActivityDate = result.activity_date;
    } else {
      stepCount = Math.max(stepCount, result.steps);
    }
    stepGoal = result.goal;
    stepRewarded = result.rewarded;
    const statusNode = document.querySelector('#step-counter-status');
    if (statusNode) delete statusNode.dataset.error;
    renderStepCounter();
    return result;
  }

  async function syncStepCount() {
    if (stepSyncBusy || !stepActivityDate || !stepSensorActive) return;
    stepSyncBusy = true;
    try {
      const result = await request('/steps/sync', {
        method: 'POST',
        body: JSON.stringify({ activity_date: stepActivityDate, steps: stepCount })
      });
      stepCount = result.steps;
      stepRewarded = result.rewarded;
      stepActivityDate = result.activity_date;
      const statusNode = document.querySelector('#step-counter-status');
      if (statusNode) delete statusNode.dataset.error;
      renderStepCounter();
      if (result.rewarded_now) {
        const dashboard = await request('/dashboard');
        window.setCitizenDashboard(dashboard);
        notifyUser('¡Meta de pasos alcanzada!', 'Has recibido 30 EcoPunts por alcanzar 5.000 pasos hoy.');
        setStatus('Meta diaria alcanzada: +30 EcoPunts.', 'connected');
      }
    } catch (error) {
      const statusNode = document.querySelector('#step-counter-status');
      if (statusNode) {
        statusNode.dataset.error = 'true';
        statusNode.textContent = getApiErrorMessage(error);
      }
      if (/El día de actividad ha cambiado/.test(error.message)) {
        stepActivityDate = null;
        try {
          await loadTodaySteps();
        } catch (refreshError) {
          console.error('No se pudo actualizar el contador de pasos del nuevo día.', refreshError);
        }
      }
    } finally {
      stepSyncBusy = false;
    }
  }

  function handleDeviceMotion(event) {
    const acceleration = event.acceleration;
    const accelerationWithGravity = event.accelerationIncludingGravity;
    const source = acceleration && acceleration.x !== null && acceleration.y !== null && acceleration.z !== null
      ? acceleration
      : accelerationWithGravity;
    if (!source || source.x === null || source.y === null || source.z === null) return;
    const magnitude = Math.hypot(source.x, source.y, source.z);
    if (stepMotionBaseline === null) stepMotionBaseline = magnitude;
    const dynamicAcceleration = magnitude - stepMotionBaseline;
    stepMotionBaseline = stepMotionBaseline * 0.9 + magnitude * 0.1;
    const now = performance.now();
    if (dynamicAcceleration < 0.35) stepMotionArmed = true;
    if (dynamicAcceleration > 1.2 && stepMotionArmed && now - lastDetectedStepAt >= 300) {
      stepMotionArmed = false;
      lastDetectedStepAt = now;
      stepCount += 1;
      renderStepCounter();
      if (stepCount >= stepGoal && !stepRewarded) void syncStepCount();
    }
  }

  async function startStepCounter(button) {
    const motionEvent = window.DeviceMotionEvent;
    const statusNode = document.querySelector('#step-counter-status');
    if (!window.isSecureContext || !motionEvent) {
      if (statusNode) statusNode.textContent = 'Este navegador no permite leer el acelerómetro. Usa un dispositivo compatible y una conexión segura (HTTPS).';
      return;
    }
    if (stepSensorActive) {
      window.removeEventListener('devicemotion', handleDeviceMotion);
      clearInterval(stepSyncTimer);
      stepSyncTimer = null;
      await syncStepCount();
      stepSensorActive = false;
      renderStepCounter();
      return;
    }

    try {
      if (typeof motionEvent.requestPermission === 'function') {
        const permission = await motionEvent.requestPermission();
        if (permission !== 'granted') throw new Error('Da permiso al acelerómetro para contar pasos.');
      }
      const current = await loadTodaySteps();
      if (!current.rewarded) {
        stepSensorActive = true;
        stepMotionBaseline = null;
        stepMotionArmed = true;
        lastDetectedStepAt = 0;
        window.addEventListener('devicemotion', handleDeviceMotion);
        stepSyncTimer = setInterval(syncStepCount, 15000);
        renderStepCounter();
      }
    } catch (error) {
      if (statusNode) {
        statusNode.dataset.error = 'true';
        statusNode.textContent = getApiErrorMessage(error);
      }
      button.disabled = false;
    }
  }

  document.querySelector('#start-step-counter')?.addEventListener('click', event => {
    const button = event.currentTarget;
    button.disabled = true;
    startStepCounter(button).finally(() => {
      if (button.isConnected) button.disabled = false;
    });
  });

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      void syncStepCount();
      return;
    }
    if (stepSensorActive) {
      loadTodaySteps().catch(error => {
        console.error('No se pudo cargar el contador de pasos al volver a la app.', error);
      });
    }
  });

  async function apiRedeemReward(id) {
    const reward = rewards.find(item => item.id === id);
    if (!reward) return;
    if (!window.confirm(`¿Quieres canjear "${reward.name}" por ${reward.cost} EcoPuntos?`)) return;
    try {
      await request('/coupons', { method: 'POST', body: JSON.stringify({ reward_id: id }) });
      await refreshWallet();
      setStatus('Cupón creado y saldo actualizado en el servidor.', 'connected');
      notifyUser('Recompensa activada', `${reward.name} ya está en tu cartera.`);
    } catch (error) {
      setStatus(getApiErrorMessage(error), 'error');
    }
  }

  async function simulateEcoScan(button) {
    button.disabled = true;
    try {
      await request('/demo/eco-scan', { method: 'POST' });
      const dashboard = await request('/dashboard');
      window.setCitizenDashboard(dashboard);
      setStatus('Escaneo de prueba registrado en SQLite · +10 EcoPuntos.', 'demo');
      document.querySelector('#close-id')?.click();
    } catch (error) {
      setStatus(getApiErrorMessage(error), 'error');
      button.disabled = false;
    }
  }

  document.addEventListener('click', event => {
    if (event.target.closest('#open-id') && liveApi) {
      event.preventDefault();
      event.stopImmediatePropagation();
      openLiveEcoId();
      return;
    }
    if (event.target.closest('#open-id')) {
      setTimeout(() => {
        const description = document.querySelector('#id-modal .modal > p');
        if (description) description.textContent = 'QR de demostración sin firma TOTP; no genera puntos reales. El canje válido debe confirmarlo la caja del comercio.';
      }, 0);
    }
    const ecoScan = event.target.closest('#scan-demo');
    if (ecoScan && liveApi) {
      event.preventDefault();
      event.stopImmediatePropagation();
      simulateEcoScan(ecoScan);
      return;
    }
    if (event.target.closest('#account, [data-account]')) {
      if (profile) openProfileDialog();
      else openAuthDialog();
      return;
    }
    const reward = event.target.closest('[data-redeem]');
    if (reward && liveApi) {
      event.preventDefault();
      event.stopImmediatePropagation();
      apiRedeemReward(reward.dataset.redeem);
      return;
    }
    if (event.target.closest('.user') && profile) openProfileDialog(true);
  }, true);

  document.addEventListener('click', event => {
    const shopButton = event.target.closest('[data-shop]');
    if (!shopButton) return;
    const merchant = merchantCatalog.find(item => item.name === shopButton.dataset.shop);
    if (!merchant) return;
    setTimeout(() => {
      const detail = document.querySelector('#detail');
      detail.querySelector('.source-note')?.remove();
      const source = document.createElement('small');
      source.className = 'source-note';
      if (merchant.is_demo) {
        source.textContent = 'Ficha ilustrativa; no es un comercio verificado.';
      } else {
        const link = document.createElement('a');
        link.href = merchant.source_url;
        link.target = '_blank';
        link.rel = 'noreferrer';
        link.textContent = `Ubicación contrastada en ${merchant.source}`;
        source.append(link);
      }
      detail.append(source);
      detail.querySelector('.map-directions')?.remove();
      if (!merchant.is_demo && merchant.latitude != null && merchant.longitude != null) {
        const directions = document.createElement('a');
        directions.className = 'map-directions';
        directions.href = `https://www.openstreetmap.org/directions?to=${encodeURIComponent(`${merchant.latitude},${merchant.longitude}`)}`;
        directions.target = '_blank';
        directions.rel = 'noreferrer';
        directions.textContent = 'Cómo llegar';
        detail.append(directions);
      }
    }, 0);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.querySelector('#profile-dialog')) closeProfileDialog();
    const userFocused = document.activeElement === document.querySelector('.user');
    if (userFocused && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      if (profile) openProfileDialog(true);
    }
  });

  const locationButton = document.querySelector('#locate');
  if (locationButton) {
    const freshButton = locationButton.cloneNode(true);
    locationButton.replaceWith(freshButton);
    freshButton.addEventListener('click', () => {
      if (!navigator.geolocation) return setStatus('Este navegador no permite consultar la ubicación.', 'error');
      setStatus('Esperando permiso de ubicación…', 'connected');
      navigator.geolocation.getCurrentPosition(position => {
        window.setCitizenLocation(position.coords.latitude, position.coords.longitude);
        setStatus('Ubicación usada solo en esta sesión; no se envió al servidor.', 'connected');
      }, error => {
        setStatus(error.code === error.PERMISSION_DENIED ? 'No se concedió el permiso de ubicación.' : 'No se pudo determinar la ubicación.', 'error');
      }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
    });
  }

  const notifications = document.querySelector('#notify');
  if (notifications) {
    const freshButton = notifications.cloneNode(true);
    notifications.replaceWith(freshButton);
    freshButton.addEventListener('click', async () => {
      const granted = await enableNotifications();
      if (granted) {
        notifyUser('Notificaciones activadas', 'Recibirás avisos de cupones y promociones en este dispositivo.');
        setStatus('Notificaciones activadas para recordatorios y promociones.', 'connected');
      } else {
        setStatus('Las notificaciones quedaron desactivadas, pero el panel de alertas seguirá funcionando localmente.', 'demo');
      }
    });
  }

  async function initialize() {
    void registerServiceWorker();
    setConnectionState(navigator.onLine);
    if (token) {
      try {
        const linkStatus = await request('/auth/google/link-status');
        if (linkStatus.link_required) {
          openAuthDialog(true, linkStatus);
          return;
        }
        const savedProfile = await request('/profile');
        updateProfileUi(savedProfile);
        liveApi = true;
        await loadAccount();
        document.body.classList.remove('auth-locked');
        if (savedProfile.password_setup_required) openCitizenCredentials();
        else openOnboarding();
        return;
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        token = null;
      }
    }
    openAuthDialog();
    try {
      await request('/health');
      setStatus('Inicia sesión para acceder a VilaCircula.', 'connected');
    } catch {
      setStatus('API no disponible · comprueba la conexión antes de iniciar sesión.', 'error');
    }
  }

  const citizenButton = document.querySelector('.user');
  citizenButton.setAttribute('role', 'button');
  citizenButton.setAttribute('aria-label', 'Abrir perfil y zona de caja');
  citizenButton.tabIndex = 0;
  window.addEventListener('offline', () => setConnectionState(false));
  window.addEventListener('online', () => setConnectionState(true));
  initialize();
})();
