"""
Templates para emails del sistema.
TODO: Implementar templates HTML con diseño responsivo.
"""

def get_verification_email_template(email: str, token: str) -> dict:
    """
    Template para email de verificación.
    TODO: Mejorar el diseño y agregar más información.
    """
    return {
        "subject": "Verifica tu email en Padelyzer",
        "html": f"""
        <html>
            <body>
                <h1>Bienvenido a Padelyzer</h1>
                <p>Hola,</p>
                <p>Gracias por registrarte en Padelyzer. Para verificar tu email, haz clic en el siguiente enlace:</p>
                <p><a href="https://padelyzer.com/verify-email?token={token}">Verificar email</a></p>
                <p>Este enlace expirará en 24 horas.</p>
                <p>Si no has creado una cuenta en Padelyzer, puedes ignorar este email.</p>
                <p>Saludos,<br>El equipo de Padelyzer</p>
            </body>
        </html>
        """,
        "text": f"""
        Bienvenido a Padelyzer

        Hola,

        Gracias por registrarte en Padelyzer. Para verificar tu email, visita el siguiente enlace:
        https://padelyzer.com/verify-email?token={token}

        Este enlace expirará en 24 horas.

        Si no has creado una cuenta en Padelyzer, puedes ignorar este email.

        Saludos,
        El equipo de Padelyzer
        """
    }

def get_password_reset_email_template(email: str, token: str) -> dict:
    """
    Template para email de recuperación de contraseña.
    TODO: Mejorar el diseño y agregar más información.
    """
    return {
        "subject": "Recuperación de contraseña en Padelyzer",
        "html": f"""
        <html>
            <body>
                <h1>Recuperación de contraseña</h1>
                <p>Hola,</p>
                <p>Has solicitado restablecer tu contraseña en Padelyzer. Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
                <p><a href="https://padelyzer.com/reset-password?token={token}">Restablecer contraseña</a></p>
                <p>Este enlace expirará en 1 hora.</p>
                <p>Si no has solicitado restablecer tu contraseña, puedes ignorar este email.</p>
                <p>Saludos,<br>El equipo de Padelyzer</p>
            </body>
        </html>
        """,
        "text": f"""
        Recuperación de contraseña

        Hola,

        Has solicitado restablecer tu contraseña en Padelyzer. Visita el siguiente enlace para crear una nueva contraseña:
        https://padelyzer.com/reset-password?token={token}

        Este enlace expirará en 1 hora.

        Si no has solicitado restablecer tu contraseña, puedes ignorar este email.

        Saludos,
        El equipo de Padelyzer
        """
    } 