(() => {
  const TOKEN_KEY = 'vilacircula-api-token';
  const PROFILE_KEY = 'vilacircula-local-profile';
  const API = '/api/v1';
  const status = document.createElement('div');
  status.className = 'api-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.textContent = 'Modo de demostración';
  document.querySelector('.topbar').after(status);
  const style = document.createElement('link');
  style.rel = 'stylesheet';
  style.href = './api-client.css';
  document.head.append(style);
  const cashierStyle = document.createElement('link');
  cashierStyle.rel = 'stylesheet';
  cashierStyle.href = './cashier.css';
  document.head.append(cashierStyle);

  let token = localStorage.getItem(TOKEN_KEY);
  let profile = null;
  let liveApi = false;
  let rewards = [];
  let merchantCatalog = [];

  async function request(path, options = {}) {
    return requestWithToken(path, options, token);
  }

  async function requestWithToken(path, options = {}, bearerToken = null) {
    const headers = new Headers(options.headers || {});
    if (bearerToken) headers.set('Authorization', `Bearer ${bearerToken}`);
    if (options.body) headers.set('Content-Type', 'application/json');
    const response = await fetch(`${API}${path}`, { ...options, headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Error del servidor (${response.status}).`);
    return payload;
  }

  function setStatus(message, mode = 'demo') {
    status.textContent = message;
    status.dataset.mode = mode;
  }

  function fallbackProfile() {
    try {
      return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null');
    } catch {
      return null;
    }
  }

  function updateProfileUi(value) {
    profile = value;
    window.applyCitizenProfile(value.display_name, value.school);
  }

  function haversineDistance(first, second) {
    const radians = Math.PI / 180;
    const lat1 = first.latitude * radians;
    const lat2 = second.latitude * radians;
    const deltaLat = (second.latitude - first.latitude) * radians;
    const deltaLon = (second.longitude - first.longitude) * radians;
    const arc = Math.sin(deltaLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) ** 2;
    return Math.round(6371000 * 2 * Math.atan2(Math.sqrt(arc), Math.sqrt(1 - arc)) / 50) * 50;
  }

  function decorateMerchants(entries) {
    const goar = { latitude: 41.3229755, longitude: 2.0066907 };
    return entries.map(merchant => ({
      ...merchant,
      distance: merchant.latitude == null ? null : `${haversineDistance(goar, merchant)} m`
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
    window.setCitizenMerchants(decorateMerchants(merchantData.items));
    window.setCitizenWallet(rewards, wallet.active, wallet.redeemed);
    setStatus('Perfil de este dispositivo · 150 puntos iniciales y ofertas de prueba. Comercios geolocalizados desde OpenStreetMap.', 'connected');
  }

  function closeProfileDialog() {
    document.querySelector('#profile-dialog')?.remove();
  }

  function openAuthDialog(mode = 'login') {
    closeProfileDialog();
    const signup = mode === 'signup';
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><span class="eyebrow">VILADECANS · PERFIL CIUDADANO</span><h2 id="profile-title">${signup ? 'Crea tu cuenta.' : 'Entra en VilaCircula.'}</h2><p>Sin correo electrónico. Usa tu nombre de usuario y contraseña.</p><form id="profile-form">${signup ? '<label for="citizen-name">Nombre o apodo</label><input id="citizen-name" name="display_name" maxlength="32" autocomplete="nickname" required value="Sergi"><label for="citizen-school">Tu instituto</label><select id="citizen-school" name="school" required><option>Goar</option><option>Torre-roja</option><option>Josep Mestres</option><option>Miramar</option><option>Olímpia</option><option>Sales</option></select>' : ''}<label for="citizen-username">Nombre de usuario</label><input id="citizen-username" name="username" minlength="3" maxlength="24" pattern="[A-Za-z0-9._\\-]+" autocomplete="username" required ${signup ? 'value="sergi"' : ''}><label for="citizen-password">Contraseña</label><input id="citizen-password" name="password" type="password" minlength="10" maxlength="128" autocomplete="${signup ? 'new-password' : 'current-password'}" required><p class="profile-privacy">${signup ? 'Mínimo 10 caracteres. El saldo y los cupones quedan en tu cuenta.' : 'La contraseña se verifica en el servidor; no se almacena en el navegador.'}</p><button class="primary profile-submit" id="profile-submit" type="submit">${signup ? 'Crear cuenta' : 'Iniciar sesión'}</button><p class="profile-error" id="profile-error" role="alert"></p></form><button class="profile-local" id="auth-switch">${signup ? 'Ya tengo una cuenta' : 'Crear una cuenta'}</button>${signup ? '<button class="profile-local" id="profile-local">Probar sin servidor · datos locales</button>' : ''}</section>`;
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    overlay.querySelector('#auth-switch').addEventListener('click', () => openAuthDialog(signup ? 'login' : 'signup'));
    overlay.addEventListener('click', event => { if (event.target === overlay && token) closeProfileDialog(); });
    overlay.querySelector('#profile-form').addEventListener('submit', async event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const values = {
        username: String(data.get('username')).trim(),
        password: String(data.get('password'))
      };
      const submit = overlay.querySelector('#profile-submit');
      submit.disabled = true;
      overlay.querySelector('#profile-error').textContent = '';
      try {
        const result = signup
          ? await request('/profiles', { method: 'POST', body: JSON.stringify({
            ...values,
            display_name: String(data.get('display_name')).trim(),
            school: String(data.get('school'))
          }) })
          : await request('/auth/login', { method: 'POST', body: JSON.stringify(values) });
        token = result.token;
        localStorage.setItem(TOKEN_KEY, token);
        localStorage.removeItem(PROFILE_KEY);
        liveApi = true;
        updateProfileUi(result.profile || result);
        await loadAccount();
        closeProfileDialog();
      } catch (error) {
        overlay.querySelector('#profile-error').textContent = error.message;
        submit.disabled = false;
      }
    });
    overlay.querySelector('#profile-local')?.addEventListener('click', () => {
      const saved = { display_name: overlay.querySelector('#citizen-name').value.trim() || 'Sergi', school: overlay.querySelector('#citizen-school').value };
      localStorage.setItem(PROFILE_KEY, JSON.stringify(saved));
      updateProfileUi(saved);
      window.setCitizenLocalDemo();
      setStatus('Modo local · saldo y cupones solo en este dispositivo.', 'demo');
      closeProfileDialog();
    });
  }

  function openProfileDialog() {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button class="icon-button modal-close" id="profile-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">PERFIL VILACIRCULA</span><h2 id="profile-title">Tu cuenta</h2><p>${profile?.display_name || ''} · ${profile?.username || 'Modo local'}</p><div class="profile-actions"><button class="profile-action" id="edit-citizen-profile"><i data-lucide="user-round-cog"></i>Editar nombre e instituto</button><button class="profile-action" id="edit-citizen-credentials"><i data-lucide="key-round"></i>Usuario y contraseña</button><button class="profile-action" id="open-cashier"><i data-lucide="store"></i>Zona de caja de comercio</button><button class="profile-action danger" id="citizen-logout"><i data-lucide="log-out"></i>Cerrar sesión</button></div><p class="profile-error" id="profile-error" role="alert"></p></section>`;
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    overlay.querySelector('#profile-close').addEventListener('click', closeProfileDialog);
    overlay.addEventListener('click', event => { if (event.target === overlay) closeProfileDialog(); });
    overlay.querySelector('#edit-citizen-profile').addEventListener('click', () => openEditCitizenProfile());
    overlay.querySelector('#edit-citizen-credentials').addEventListener('click', () => openCitizenCredentials());
    overlay.querySelector('#open-cashier').addEventListener('click', openCashierLogin);
    overlay.querySelector('#citizen-logout').addEventListener('click', logoutCitizen);
  }

  function openEditCitizenProfile() {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button class="icon-button modal-close" id="profile-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">PERFIL CIUDADANO</span><h2 id="profile-title">Editar perfil</h2><form id="profile-form"><label for="citizen-name">Nombre o apodo</label><input id="citizen-name" name="display_name" maxlength="32" required><label for="citizen-school">Tu instituto</label><select id="citizen-school" name="school" required><option>Goar</option><option>Torre-roja</option><option>Josep Mestres</option><option>Miramar</option><option>Olímpia</option><option>Sales</option></select><button class="primary profile-submit" type="submit">Guardar cambios</button><p class="profile-error" id="profile-error" role="alert"></p></form></section>`;
    document.querySelector('#modal-root').append(overlay);
    overlay.querySelector('#citizen-name').value = profile?.display_name || '';
    overlay.querySelector('#citizen-school').value = profile?.school || 'Goar';
    overlay.querySelector('#profile-close').addEventListener('click', openProfileDialog);
    overlay.querySelector('#profile-form').addEventListener('submit', async event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const submit = overlay.querySelector('.profile-submit');
      submit.disabled = true;
      try {
        const saved = await request('/profile', { method: 'PUT', body: JSON.stringify({ display_name: String(data.get('display_name')).trim(), school: String(data.get('school')) }) });
        updateProfileUi({ ...profile, ...saved });
        closeProfileDialog();
      } catch (error) {
        overlay.querySelector('#profile-error').textContent = error.message;
        submit.disabled = false;
      }
    });
  }

  function openCitizenCredentials() {
    closeProfileDialog();
    const needsSetup = Boolean(profile?.password_setup_required);
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-title"><button class="icon-button modal-close" id="profile-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">SEGURIDAD DE CUENTA</span><h2 id="profile-title">${needsSetup ? 'Protege tu cuenta.' : 'Cambiar credenciales'}</h2>${needsSetup ? '<p>Este perfil venía de la versión anterior. Añade usuario y contraseña antes de continuar.</p>' : ''}<form id="credentials-form"><label for="account-username">Nombre de usuario</label><input id="account-username" name="username" minlength="3" maxlength="24" pattern="[A-Za-z0-9._\\-]+" autocomplete="username" required><label for="current-password">Contraseña actual${needsSetup ? ' (no configurada)' : ''}</label><input id="current-password" name="current_password" type="password" autocomplete="current-password" ${needsSetup ? '' : 'required'}><label for="new-password">${needsSetup ? 'Crea una contraseña' : 'Nueva contraseña'}</label><input id="new-password" name="password" type="password" minlength="10" maxlength="128" autocomplete="new-password" required><button class="primary profile-submit" type="submit">Guardar credenciales</button><p class="profile-error" id="profile-error" role="alert"></p></form></section>`;
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
        profile.password_setup_required = false;
        closeProfileDialog();
        setStatus('Credenciales actualizadas; las otras sesiones se han cerrado.', 'connected');
      } catch (error) {
        overlay.querySelector('#profile-error').textContent = error.message;
        submit.disabled = false;
      }
    });
  }

  async function logoutCitizen() {
    try {
      await request('/auth/logout', { method: 'POST' });
    } catch {
      // A server-side expiry still clears the local session.
    }
    token = null;
    profile = null;
    liveApi = false;
    localStorage.removeItem(TOKEN_KEY);
    closeProfileDialog();
    openAuthDialog('login');
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
      submit.disabled = true;
      try {
        const result = await requestWithToken('/auth/cashier/login', {
          method: 'POST',
          body: JSON.stringify({ username: String(data.get('username')).trim(), password: String(data.get('password')) })
        }, null);
        sessionStorage.setItem('vilacircula-cashier-token', result.token);
        if (result.must_change_password) return openCashierPassword(result.token, result.merchant);
        openCashierConsole(result.token, result.merchant);
      } catch (error) {
        overlay.querySelector('#cashier-error').textContent = error.message;
        submit.disabled = false;
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
      if (password !== data.get('confirmation')) {
        overlay.querySelector('#cashier-password-error').textContent = 'Las contraseñas no coinciden.';
        return;
      }
      submit.disabled = true;
      try {
        const result = await requestWithToken('/cashier/password', { method: 'PUT', body: JSON.stringify({ password, current_password: String(data.get('current_password') || '') || null }) }, cashierToken);
        sessionStorage.setItem('vilacircula-cashier-token', result.token);
        const updated = await requestWithToken('/cashier/me', {}, result.token);
        openCashierConsole(result.token, updated);
      } catch (error) {
        overlay.querySelector('#cashier-password-error').textContent = error.message;
        submit.disabled = false;
      }
    });
  }

  let cashierStream;
  let cashierFrame;
  let cashierCanvas;
  let cashierScanning = false;
  let cashierLastCode = null;
  let cashierLastAt = 0;

  async function startCashierScanner(cashierToken, statusNode, video, preview) {
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Este navegador no permite usar la cámara.');
      cashierStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
      video.srcObject = cashierStream;
      await video.play();
      preview.hidden = false;
      cashierCanvas = document.createElement('canvas');
      cashierScanning = true;
      let detector;
      if ('BarcodeDetector' in window) detector = new BarcodeDetector({ formats: ['qr_code'] });
      else if (!window.jsQR) await loadScript('https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js');
      const scan = async () => {
        if (!cashierScanning) return;
        try {
          let rawValue;
          if (detector) {
            rawValue = (await detector.detect(video))[0]?.rawValue;
          } else if (video.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
            cashierCanvas.width = video.videoWidth;
            cashierCanvas.height = video.videoHeight;
            const context = cashierCanvas.getContext('2d', { willReadFrequently: true });
            context.drawImage(video, 0, 0, cashierCanvas.width, cashierCanvas.height);
            rawValue = window.jsQR(context.getImageData(0, 0, cashierCanvas.width, cashierCanvas.height).data, cashierCanvas.width, cashierCanvas.height)?.data;
          }
          if (rawValue) {
            const code = rawValue.match(/VC-[A-Z0-9]{5,32}/i)?.[0]?.toUpperCase();
            if (!code) {
              statusNode.textContent = 'El QR no contiene un cupón VilaCircula.';
            } else {
              if (code === cashierLastCode && Date.now() - cashierLastAt < 3000) {
                cashierFrame = requestAnimationFrame(scan);
                return;
              }
              cashierLastCode = code;
              cashierLastAt = Date.now();
              const result = await requestWithToken('/cashier/coupons/redeem', {
                method: 'POST',
                body: JSON.stringify({ code })
              }, cashierToken);
              statusNode.textContent = `Cupón validado: ${result.coupon.name} · ${result.merchant}.`;
              if ('vibrate' in navigator) navigator.vibrate([80, 40, 80]);
            }
          }
        } catch (error) {
          statusNode.textContent = error.message;
          if (error.message.includes('401')) cashierScanning = false;
        }
        if (cashierScanning) cashierFrame = requestAnimationFrame(scan);
      };
      scan();
    } catch (error) {
      statusNode.textContent = error.name === 'NotAllowedError' ? 'Permite el acceso a la cámara para escanear.' : error.message;
    }
  }

  function stopCashierScanner() {
    cashierScanning = false;
    if (cashierFrame) cancelAnimationFrame(cashierFrame);
    cashierStream?.getTracks().forEach(track => track.stop());
    cashierStream = null;
  }

  function openCashierConsole(cashierToken, cashier) {
    closeProfileDialog();
    const overlay = document.createElement('div');
    overlay.id = 'profile-dialog';
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="modal cashier-console" role="dialog" aria-modal="true" aria-labelledby="cashier-title"><button class="icon-button modal-close" id="cashier-close" aria-label="Cerrar"><i data-lucide="x"></i></button><span class="eyebrow">VILA CIRCULA · CAJA AUTORIZADA</span><h2 id="cashier-title">${cashier.merchant_name}</h2><p>Los cupones se validan contra este comercio; un cupón de otra tienda será rechazado.</p><div class="cashier-preview" id="cashier-preview" hidden><video id="cashier-video" playsinline muted></video><span class="scan-frame"></span></div><p class="scanner-status" id="cashier-status">Cámara apagada. Se solicitará permiso al empezar a escanear.</p><div class="coupon-modal-actions"><button class="primary" id="cashier-start-scan"><i data-lucide="scan-line"></i>Escanear cupón</button><button class="redeem" id="cashier-change-password">Cambiar contraseña</button></div><button class="profile-local" id="cashier-logout">Cerrar sesión de caja</button></section>`;
    document.querySelector('#modal-root').append(overlay);
    window.lucide?.createIcons();
    overlay.querySelector('#cashier-close').addEventListener('click', () => { stopCashierScanner(); openProfileDialog(); });
    overlay.querySelector('#cashier-start-scan').addEventListener('click', () => startCashierScanner(cashierToken, overlay.querySelector('#cashier-status'), overlay.querySelector('#cashier-video'), overlay.querySelector('#cashier-preview')));
    overlay.querySelector('#cashier-change-password').addEventListener('click', () => {
      stopCashierScanner();
      openCashierPassword(cashierToken, cashier);
    });
    overlay.querySelector('#cashier-logout').addEventListener('click', async () => {
      stopCashierScanner();
      try {
        await requestWithToken('/auth/cashier/logout', { method: 'POST' }, cashierToken);
      } catch {
        // Clear the local cashier session even if the server is unreachable.
      }
      sessionStorage.removeItem('vilacircula-cashier-token');
      openProfileDialog();
    });
  }

  async function refreshWallet() {
    const [dashboard, wallet] = await Promise.all([request('/dashboard'), request('/coupons')]);
    window.setCitizenDashboard(dashboard);
    window.setCitizenWallet(rewards, wallet.active, wallet.redeemed);
  }

  window.apiCouponRedeem = async code => {
    try {
      const result = await request('/coupons/redeem', { method: 'POST', body: JSON.stringify({ code }) });
      await refreshWallet();
      window.closeCitizenCouponModal();
      setStatus(result.is_demo ? 'Canje de prueba registrado en el servidor.' : 'Cupón validado por el servidor.', result.is_demo ? 'demo' : 'connected');
      if ('vibrate' in navigator) navigator.vibrate([70, 35, 70]);
      return true;
    } catch (error) {
      const scannerStatus = document.querySelector('#scanner-status');
      if (scannerStatus) scannerStatus.textContent = error.message;
      else setStatus(error.message, 'error');
      return false;
    }
  };

  async function apiRedeemReward(id) {
    try {
      await request('/coupons', { method: 'POST', body: JSON.stringify({ reward_id: id }) });
      await refreshWallet();
      setStatus('Cupón creado y saldo actualizado en el servidor.', 'connected');
    } catch (error) {
      setStatus(error.message, 'error');
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
      setStatus(error.message, 'error');
      button.disabled = false;
    }
  }

  document.addEventListener('click', event => {
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
    freshButton.addEventListener('click', () => setStatus('Los avisos push aún no están configurados; no se solicita permiso al dispositivo.', 'demo'));
  }

  async function initialize() {
    if (token) {
      try {
        const savedProfile = await request('/profile');
        updateProfileUi(savedProfile);
        liveApi = true;
        await loadAccount();
        if (savedProfile.password_setup_required) openCitizenCredentials();
        return;
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        token = null;
      }
    }
    const localProfile = fallbackProfile();
    if (localProfile) {
      profile = localProfile;
      updateProfileUi(localProfile);
      window.setCitizenLocalDemo();
      setStatus('Modo local · saldo y cupones solo en este dispositivo.', 'demo');
    }
    try {
      await request('/health');
      setStatus('Inicia sesión con tu usuario y contraseña.', 'connected');
      openAuthDialog('login');
    } catch {
      if (!localProfile) openAuthDialog('signup');
      setStatus('API no disponible · crea un perfil local de demostración.', 'error');
    }
  }

  const citizenButton = document.querySelector('.user');
  citizenButton.setAttribute('role', 'button');
  citizenButton.setAttribute('aria-label', 'Abrir perfil y zona de caja');
  citizenButton.tabIndex = 0;
  initialize();
})();
