document.addEventListener(DOMContentLoaded, () = {
  const form = document.getElementById(registroForm);

   Toggle password visibility
  document.querySelectorAll([data-toggle]).forEach(btn = {
    btn.addEventListener(click, () = {
      const id = btn.getAttribute(data-toggle);
      const input = document.getElementById(id);
      if (input) input.type = input.type === password  text  password;
    });
  });

   Validación avanzada
  form.addEventListener(submit, (e) = {
    e.preventDefault();

    const email = document.getElementById(email).value.trim();
    const pass = document.getElementById(password).value.trim();
    const confirm = document.getElementById(confirm_password).value.trim();

    const emailPattern = ^[^s@]+@[^s@]+.[^s@]{2,}$;

    if (!emailPattern.test(email)) {
      showError(Correo electrónico inválido.);
      return;
    }
    if (pass.length  6) {
      showError(La contraseña debe tener al menos 6 caracteres.);
      return;
    }
    if (pass !== confirm) {
      showError(Las contraseñas no coinciden.);
      return;
    }

     Animación de envío
    form.classList.add(opacity-50, pointer-events-none);
    form.submit();
  });

  function showError(msg) {
    alert(msg);  Aquí podés poner un modal o notificación
  }
});
