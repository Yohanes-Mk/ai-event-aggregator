"""
HTML email renderer — email-client safe (inline styles, table layout, no CSS vars).
Palette mirrors the dashboard: dark bg, amber for videos, teal for events.
"""
from __future__ import annotations

from agent.youtube_email_agent import YouTubeEmailResult
from agent.events_email_agent import EventsEmailResult

# ── Palette (hardcoded — no CSS vars in email) ────────────────────────────────
BG        = "#07070a"
SURFACE   = "#0e0e16"
BORDER    = "#1e1e26"
TEXT      = "#e8e2d9"
MUTED     = "#7a7688"
AMBER     = "#e8a020"
TEAL      = "#18c4a0"
SCORE_HI  = "#f0c43a"
SCORE_MID = "#e8a020"
SCORE_LOW = "#e05a20"


def _score_color(n: int) -> str:
    if n >= 85: return SCORE_HI
    if n >= 70: return SCORE_MID
    return SCORE_LOW


def _tag(text: str, accent: str) -> str:
    return (
        f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;'
        f'background:#14141f;border:1px solid {BORDER};border-radius:2px;'
        f'font-family:monospace;font-size:11px;color:{accent};">{text}</span>'
    )


def _email_shell(accent: str, subject_label: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <meta name="color-scheme" content="dark"/>
  <title>{subject_label}</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:Georgia,'Times New Roman',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:{BG};min-height:100vh;">
    <tr><td align="center" style="padding:32px 16px;">

      <!-- Container -->
      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="padding:0 0 24px 0;border-bottom:1px solid {BORDER};">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <span style="font-family:Georgia,serif;font-size:22px;font-weight:900;
                                letter-spacing:0.18em;color:{TEXT};">THE
                    <span style="color:{accent};">STACK</span>
                  </span>
                </td>
                <td align="right">
                  <span style="font-family:monospace;font-size:11px;color:{MUTED};
                                letter-spacing:0.08em;">AI DIGEST</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Body -->
        <tr><td style="padding:32px 0;">{body_html}</td></tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 0 0 0;border-top:1px solid {BORDER};">
            <p style="margin:0;font-family:monospace;font-size:11px;
                      color:{MUTED};letter-spacing:0.08em;">
              THE STACK · Personal AI Digest · Curated for Yohannes
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── YouTube Email ─────────────────────────────────────────────────────────────

def render_youtube_email(result: YouTubeEmailResult) -> str:
    rows = []

    # Greeting + intro
    rows.append(f"""
      <p style="margin:0 0 6px 0;font-size:18px;color:{TEXT};">{result.greeting}</p>
      <p style="margin:0 0 32px 0;font-size:14px;color:{MUTED};line-height:1.6;">{result.introduction}</p>
    """)

    for article in result.articles:
        score_color = _score_color(article.score)
        tags_html = "".join(_tag(t, AMBER) for t in article.tools_concepts)

        rows.append(f"""
      <!-- Video Card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="margin-bottom:12px;background:{SURFACE};
                    border:1px solid {BORDER};border-left:3px solid {AMBER};">
        <tr>
          <!-- Content -->
          <td style="padding:20px 16px 20px 20px;vertical-align:top;">
            <p style="margin:0 0 6px 0;font-family:monospace;font-size:10px;
                      letter-spacing:0.12em;text-transform:uppercase;">
              <a href="{article.channel_url}" target="_blank"
                 style="color:{AMBER};text-decoration:none;">{article.channel_name}</a>
            </p>
            <h2 style="margin:0 0 10px 0;font-family:Georgia,serif;font-size:17px;
                       font-weight:700;line-height:1.3;color:{TEXT};">{article.title}</h2>
            <p style="margin:0 0 12px 0;font-size:13px;line-height:1.65;color:{MUTED};">
              {article.summary}
            </p>
            <div style="margin:0 0 10px 0;">{tags_html}</div>
            <p style="margin:0 0 14px 0;font-size:12px;font-style:italic;
                      color:#3e3c4a;border-left:2px solid {BORDER};padding-left:10px;">
              {article.ranking_reason}
            </p>
            <a href="{article.url}" target="_blank"
               style="display:inline-block;font-family:monospace;font-size:11px;
                      letter-spacing:0.08em;color:{AMBER};text-decoration:none;
                      border:1px solid {AMBER};padding:5px 14px;">
              &#9654; Watch
            </a>
          </td>
          <!-- Score -->
          <td style="padding:20px 20px 20px 0;vertical-align:top;
                     text-align:right;white-space:nowrap;">
            <span style="font-family:Georgia,serif;font-size:30px;font-weight:900;
                         line-height:1;color:{score_color};">{article.score}</span>
            <br/>
            <span style="font-family:monospace;font-size:9px;color:{MUTED};
                         letter-spacing:0.1em;">/ 100</span>
          </td>
        </tr>
      </table>
        """)

    # Signature
    rows.append(f"""
      <p style="margin:32px 0 0 0;font-size:13px;color:{MUTED};line-height:1.6;">
        {result.signature}
      </p>
    """)

    return _email_shell(AMBER, result.subject, "\n".join(rows))


# ── Events Email ──────────────────────────────────────────────────────────────

def render_events_email(result: EventsEmailResult) -> str:
    rows = []

    # Greeting + intro
    rows.append(f"""
      <p style="margin:0 0 6px 0;font-size:18px;color:{TEXT};">{result.greeting}</p>
      <p style="margin:0 0 32px 0;font-size:14px;color:{MUTED};line-height:1.6;">{result.introduction}</p>
    """)

    for event in result.events:
        score_color = _score_color(event.relevance_score)

        rows.append(f"""
      <!-- Event Card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="margin-bottom:12px;background:{SURFACE};
                    border:1px solid {BORDER};border-top:3px solid {TEAL};">
        <tr>
          <td style="padding:20px;vertical-align:top;">
            <p style="margin:0 0 6px 0;font-family:monospace;font-size:10px;
                      letter-spacing:0.1em;color:{TEAL};">
              {event.date_time}
            </p>
            <h2 style="margin:0 0 6px 0;font-family:Georgia,serif;font-size:17px;
                       font-weight:700;line-height:1.3;color:{TEXT};">{event.title}</h2>
            <p style="margin:0 0 12px 0;font-size:12px;color:{MUTED};">
              &#128205; {event.location}
            </p>
            <p style="margin:0 0 12px 0;font-size:13px;line-height:1.65;color:{MUTED};">
              {event.summary}
            </p>
            <p style="margin:0 0 14px 0;font-size:12px;font-style:italic;
                      color:#3e3c4a;border-left:2px solid {BORDER};padding-left:10px;">
              {event.ranking_reason}
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <a href="{event.url}" target="_blank"
                     style="display:inline-block;font-family:monospace;font-size:11px;
                            letter-spacing:0.08em;color:{TEAL};text-decoration:none;
                            border:1px solid {TEAL};padding:5px 14px;">
                    RSVP &#8594;
                  </a>
                </td>
                <td align="right">
                  <span style="font-family:Georgia,serif;font-size:26px;font-weight:900;
                               color:{score_color};">{event.relevance_score}</span>
                  <span style="font-family:monospace;font-size:9px;color:{MUTED};
                               letter-spacing:0.1em;">/ 100</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
        """)

    # Signature
    rows.append(f"""
      <p style="margin:32px 0 0 0;font-size:13px;color:{MUTED};line-height:1.6;">
        {result.signature}
      </p>
    """)

    return _email_shell(TEAL, result.subject, "\n".join(rows))
