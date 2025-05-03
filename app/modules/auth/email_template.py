from app.core.config import settings

def get_otp_html(otp):
    return f"""
<html>
  <head>
    <style>
      body {{
        font-family: Arial, sans-serif;
        background-color: #f9f9f9;
        padding: 20px;
        color: #333;
      }}
      .container {{
        max-width: 500px;
        margin: auto;
        background-color: #fff;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }}
      .otp-box {{
        background-color: #f0f4ff;
        color: #2d3e50;
        padding: 14px 18px;
        font-size: 22px;
        font-weight: bold;
        letter-spacing: 3px;
        text-align: center;
        border-radius: 6px;
        margin-top: 20px;
        user-select: all;
      }}
      .footer {{
        margin-top: 30px;
        font-size: 12px;
        color: #999;
        text-align: center;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h2>Email Verification</h2>
      <p>Use the OTP code below to verify your email address:</p>
      <div class="otp-box">{otp}</div>
      <p style="margin-top: 20px;">If you didn’t request this, you can safely ignore this email.</p>
      <div class="footer">
        &copy; 2025 HolidayNepal. All rights reserved.
      </div>
    </div>
  </body>
</html>
"""


def get_password_reset_html(token):
    return f"""
<html>
  <head>
    <style>
      body {{
        font-family: Arial, sans-serif;
        background-color: #f9f9f9;
        padding: 20px;
        color: #333;
      }}
      .container {{
        max-width: 500px;
        margin: auto;
        background-color: #fff;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }}
      .btn {{
        display: inline-block;
        background-color: #007bff;
        text-decoration: none;
        padding: 12px 20px;
        font-size: 16px;
        border-radius: 6px;
        margin-top: 20px;
      }}
      .footer {{
        margin-top: 30px;
        font-size: 12px;
        color: #999;
        text-align: center;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h2>Password Reset For HolidayNepal</h2>
      <p>Click the button below to reset your password:</p>
      <a href="{settings.FRONTEND_FORGET_PASSWORD_URL}/{token}" class="btn" style="color:#fff;">Reset Password</a>
      <p style="margin-top: 20px;">If you didn’t request a password reset, just ignore this email.</p>
      <div class="footer">
        &copy; 2025 HolidayNepal. All rights reserved.
      </div>
    </div>
  </body>
</html>
"""
