"""
Service d'envoi d'e-mails via Gmail SMTP (gratuit).
Nécessite un mot de passe d'application Gmail :
  myaccount.google.com → Sécurité → Mots de passe des applications
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import Report


def _build_html(report: Report, email: str) -> str:
    traits_html = ""
    for key, trait in report.traits.items():
        bar_color = "#7A9467" if trait.score > 65 else "#8B7FA8" if trait.score < 35 else "#C4A07A"
        traits_html += f"""
        <tr>
          <td style="padding:10px 0; border-bottom:1px solid #EDE8DC;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#7A9467;vertical-align:middle;margin-right:10px;"></span>
            <strong style="color:#2A2725;">{trait.label}</strong>
            <div style="background:#EDE8DC; border-radius:99px; height:6px; margin:8px 0; overflow:hidden;">
              <div style="background:{bar_color}; width:{trait.score}%; height:100%; border-radius:99px;"></div>
            </div>
            <span style="color:#9A9490; font-size:0.85rem;">{trait.interpretation}</span>
          </td>
        </tr>"""

    strengths_html = "".join(
        f'<li style="margin:6px 0; color:#6B6560;">• {s}</li>'
        for s in report.strengths
    )
    areas_html = "".join(
        f'<li style="margin:6px 0; color:#6B6560;">• {a}</li>'
        for a in report.areas_of_attention
    )
    recommendations_html = "".join(
        f'<li style="margin:8px 0; color:#6B6560; line-height:1.6;">{r}</li>'
        for r in report.recommendations
    )

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; padding:0; background:#F5F1E8; font-family:'DM Sans', Arial, sans-serif;">
  <div style="max-width:600px; margin:0 auto; padding:40px 20px;">

    <!-- En-tête -->
    <div style="text-align:center; margin-bottom:32px;">
      <div style="width:56px;height:56px;margin:0 auto 12px;border-radius:14px;background:linear-gradient(135deg,#7A9467,#C4A07A);"></div>
      <h1 style="font-family:Georgia, serif; font-weight:500; color:#2A2725; margin:0; font-size:1.6rem;">
        Votre rapport de personnalité
      </h1>
      <p style="color:#9A9490; font-size:0.9rem; margin:8px 0 0;">personAI · Test Big Five Adaptatif</p>
    </div>

    <!-- Carte archétype -->
    <div style="background:linear-gradient(135deg,#FDFCF8,#EEE8DA); border-radius:20px; padding:32px; margin-bottom:24px; box-shadow:0 8px 32px rgba(42,39,37,.10); border:1px solid rgba(122,148,103,.18);">
      <p style="font-size:0.75rem; font-weight:600; color:#7A9467; letter-spacing:.08em; text-transform:uppercase; margin:0 0 12px;">Vous êtes</p>
      <div style="display:flex; align-items:center; gap:20px; margin-bottom:16px;">
        <div style="width:64px; height:64px; flex-shrink:0; border-radius:12px; background:linear-gradient(135deg,#7A9467,#8B7FA8);"></div>
        <div>
          <h2 style="font-family:Georgia,serif; font-size:1.8rem; font-weight:500; color:#2A2725; margin:0; line-height:1.1;">{report.archetype.name}</h2>
          <p style="color:#7A9467; font-style:italic; margin:4px 0 0; font-size:0.95rem;">{report.archetype.tagline}</p>
        </div>
      </div>
      <p style="color:#6B6560; line-height:1.8; margin:0 0 16px; font-size:0.95rem;">{report.archetype.description}</p>
      <hr style="border:none; border-top:1px solid rgba(122,148,103,.2); margin:16px 0;">
      <p style="color:#6B6560; line-height:1.8; margin:0; font-size:0.95rem;">{report.overall_summary}</p>
    </div>

    <!-- Traits -->
    <div style="background:#FDFCF8; border-radius:16px; padding:24px; margin-bottom:24px; box-shadow:0 4px 16px rgba(42,39,37,.06); border:1px solid rgba(122,148,103,.18);">
      <h3 style="font-family:Georgia,serif; font-size:1.1rem; font-weight:500; color:#2A2725; margin:0 0 16px;">Vos cinq dimensions</h3>
      <table width="100%" cellpadding="0" cellspacing="0">{traits_html}</table>
    </div>

    <!-- Points forts -->
    <div style="background:#FDFCF8; border-radius:16px; padding:24px; margin-bottom:24px; box-shadow:0 4px 16px rgba(42,39,37,.06); border:1px solid rgba(122,148,103,.18);">
      <h3 style="font-family:Georgia,serif; font-size:1.1rem; font-weight:500; color:#2A2725; margin:0 0 12px;">Points forts</h3>
      <ul style="margin:0; padding:0 0 0 4px; list-style:none;">{strengths_html}</ul>
    </div>

    <!-- Points de vigilance -->
    <div style="background:#FDFCF8; border-radius:16px; padding:24px; margin-bottom:24px; box-shadow:0 4px 16px rgba(42,39,37,.06); border:1px solid rgba(139,127,168,.25);">
      <h3 style="font-family:Georgia,serif; font-size:1.1rem; font-weight:500; color:#2A2725; margin:0 0 12px;">Points de vigilance</h3>
      <ul style="margin:0; padding:0 0 0 4px; list-style:none;">{areas_html}</ul>
    </div>

    <!-- Recommandations -->
    <div style="background:#FDFCF8; border-radius:16px; padding:24px; margin-bottom:32px; box-shadow:0 4px 16px rgba(42,39,37,.06); border:1px solid rgba(122,148,103,.18);">
      <h3 style="font-family:Georgia,serif; font-size:1.1rem; font-weight:500; color:#2A2725; margin:0 0 12px;">Recommandations</h3>
      <ol style="margin:0; padding:0 0 0 20px;">{recommendations_html}</ol>
    </div>

    <!-- Footer -->
    <div style="text-align:center; padding-top:16px; border-top:1px solid #EDE8DC;">
      <p style="color:#9A9490; font-size:0.75rem; line-height:1.7;">{report.disclaimer}</p>
      <p style="color:#9A9490; font-size:0.75rem; margin-top:8px;">personAI — Test de personnalité adaptatif par IA</p>
    </div>

  </div>
</body>
</html>"""


def send_report_email(to_email: str, report: Report) -> tuple[bool, str | None]:
    """
    Envoie le rapport par e-mail via SMTP.

    Retourne (True, None) si succès, sinon (False, code) avec :
      - \"missing_credentials\" : aucun couple user/mot de passe configuré
      - \"smtp_failed\"         : erreur réseau / SMTP (détails dans les logs serveur)

    Variables d'environnement (priorité SMTP_*, sinon alias Gmail) :
      SMTP_HOST         — serveur SMTP  (défaut: smtp.gmail.com)
      SMTP_PORT         — port          (défaut: 465 ; 587 + STARTTLS si besoin)
      SMTP_USER         — adresse d'envoi
      SMTP_PASSWORD     — mot de passe ou mot de passe d'application
      SMTP_FROM_NAME    — nom affiché   (défaut: personAI Test)
      GMAIL_USER        — alias de SMTP_USER
      GMAIL_APP_PASSWORD — alias de SMTP_PASSWORD
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER") or os.getenv("GMAIL_USER")
    smtp_password = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
    from_name = os.getenv("SMTP_FROM_NAME", "personAI Test")

    if not smtp_user or not smtp_password:
        print(
            "[WARN] E-mail non envoyé : définissez SMTP_USER et SMTP_PASSWORD "
            "(ou GMAIL_USER et GMAIL_APP_PASSWORD)."
        )
        return False, "missing_credentials"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Votre rapport personAI — {report.archetype.name}"
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email

    html_content = _build_html(report, to_email)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if smtp_port == 587:
            # STARTTLS (Outlook, Yahoo, OVH…)
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
        else:
            # SSL direct (Gmail port 465, par défaut)
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[OK] E-mail envoyé à {to_email}")
        return True, None
    except Exception as e:
        print(f"[ERR] Erreur envoi e-mail : {e}")
        return False, "smtp_failed"
