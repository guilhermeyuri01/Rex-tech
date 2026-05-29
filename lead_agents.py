"""Agentes de prospecção para empresas sem site.

Este módulo cria uma arquitetura segura e extensível com três agentes:

1. GoogleMapsLeadCeoAgent: busca empresas no Google Places API (New), filtra
   negócios com boa avaliação e sem site.
2. EmailProposalAgent: envia relatório para o dono da operação e propostas
   apenas para leads aprovados/permitidos.
3. DemoSiteAgent/ReplyMonitorAgent: monitora respostas interessadas e cria uma
   landing page demonstrativa com visual 3D conforme o nicho do lead.

Observação importante: a API oficial do Google Places não fornece e-mail nem
WhatsApp de empresas. Esses campos precisam vir de uma fonte própria, CRM,
planilha autorizada ou enriquecimento compatível com LGPD/termos de uso.
"""

from __future__ import annotations

import argparse
import csv
import html
import imaplib
import json
import os
import re
import smtplib
import ssl
import textwrap
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Sequence

import requests

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
REPORTS_DIR = Path("reports")
DEMOS_DIR = Path("generated_sites")
DEFAULT_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.googleMapsUri",
        "places.nationalPhoneNumber",
        "places.rating",
        "places.userRatingCount",
        "places.primaryType",
        "places.types",
        "places.websiteUri",
    ]
)
INTEREST_KEYWORDS = (
    "quero",
    "interesse",
    "interessado",
    "interessada",
    "exemplo",
    "modelo",
    "site",
    "proposta",
    "valor",
    "preço",
    "orcamento",
    "orçamento",
)


@dataclass(slots=True)
class BusinessLead:
    """Lead de empresa candidata a receber proposta de criação de site."""

    name: str
    rating: float
    review_count: int
    address: str
    maps_url: str
    phone: str = ""
    email: str = ""
    whatsapp: str = ""
    niche: str = ""
    place_id: str = ""
    website: str = ""
    source: str = "google_places"
    consent_status: str = "needs_review"
    notes: str = ""

    @property
    def has_site(self) -> bool:
        return bool(self.website.strip())

    @property
    def is_contactable(self) -> bool:
        return bool(self.email.strip()) and self.consent_status in {
            "approved",
            "opt_in",
            "customer_requested",
        }


class GoogleMapsLeadCeoAgent:
    """Agente líder que pesquisa, filtra e consolida leads."""

    def __init__(
        self,
        api_key: str,
        min_rating: float = 4.5,
        min_reviews: int = 20,
        pause_seconds: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.min_rating = min_rating
        self.min_reviews = min_reviews
        self.pause_seconds = pause_seconds

    def search_places(self, query: str, max_pages: int = 1) -> list[dict]:
        """Consulta o Google Places Text Search (New) usando FieldMask enxuto."""
        if not self.api_key:
            raise ValueError("Defina GOOGLE_MAPS_API_KEY antes de buscar leads.")

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": DEFAULT_FIELD_MASK,
        }
        payload: dict[str, object] = {
            "textQuery": query,
            "languageCode": "pt-BR",
            "regionCode": "BR",
        }
        places: list[dict] = []

        for page_number in range(max_pages):
            response = requests.post(
                PLACES_TEXT_SEARCH_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            places.extend(data.get("places", []))

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
            payload["pageToken"] = next_page_token
            if page_number + 1 < max_pages:
                time.sleep(self.pause_seconds)

        return places

    def collect_leads(self, niches: Sequence[str], cities: Sequence[str]) -> list[BusinessLead]:
        """Busca por nicho/cidade e retorna empresas bem avaliadas sem site."""
        by_place_id: dict[str, BusinessLead] = {}

        for niche in niches:
            for city in cities:
                query = f"{niche} em {city}, Brasil"
                for place in self.search_places(query):
                    lead = self._lead_from_place(place, niche=niche)
                    if not self._is_qualified(lead):
                        continue
                    key = lead.place_id or f"{lead.name}|{lead.address}"
                    by_place_id[key] = lead

        return sorted(
            by_place_id.values(),
            key=lambda lead: (lead.rating, lead.review_count),
            reverse=True,
        )

    def _lead_from_place(self, place: dict, niche: str) -> BusinessLead:
        display_name = place.get("displayName") or {}
        return BusinessLead(
            name=display_name.get("text", "Empresa sem nome"),
            rating=float(place.get("rating") or 0),
            review_count=int(place.get("userRatingCount") or 0),
            address=place.get("formattedAddress", ""),
            maps_url=place.get("googleMapsUri", ""),
            phone=place.get("nationalPhoneNumber", ""),
            niche=niche,
            place_id=place.get("id", ""),
            website=place.get("websiteUri", ""),
            notes="E-mail/WhatsApp devem ser adicionados por fonte autorizada antes do envio.",
        )

    def _is_qualified(self, lead: BusinessLead) -> bool:
        return (
            not lead.has_site
            and lead.rating >= self.min_rating
            and lead.review_count >= self.min_reviews
        )


class LeadReportStore:
    """Persistência de relatórios em JSON e CSV."""

    def __init__(self, reports_dir: Path = REPORTS_DIR) -> None:
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save(self, leads: Sequence[BusinessLead], prefix: str = "leads") -> tuple[Path, Path]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        json_path = self.reports_dir / f"{prefix}-{timestamp}.json"
        csv_path = self.reports_dir / f"{prefix}-{timestamp}.csv"

        records = [asdict(lead) for lead in leads]
        json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

        fieldnames = list(BusinessLead.__dataclass_fields__.keys())
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        return json_path, csv_path

    @staticmethod
    def load(path: Path) -> list[BusinessLead]:
        if path.suffix.lower() == ".json":
            records = json.loads(path.read_text(encoding="utf-8"))
            return [BusinessLead(**record) for record in records]

        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return [
                BusinessLead(
                    **{
                        **row,
                        "rating": float(row.get("rating") or 0),
                        "review_count": int(row.get("review_count") or 0),
                    }
                )
                for row in reader
            ]


class EmailProposalAgent:
    """Agente que envia relatório e propostas por e-mail."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        sender_name: str = "Rex Tech",
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.sender_name = sender_name

    @classmethod
    def from_env(cls) -> "EmailProposalAgent":
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            sender_name=os.getenv("SENDER_NAME", "Rex Tech"),
        )

    def send_report(self, owner_email: str, leads: Sequence[BusinessLead], attachments: Sequence[Path]) -> None:
        subject = f"Relatório de leads sem site - {len(leads)} empresas qualificadas"
        body = self._report_body(leads)
        self._send_email(owner_email, subject, body, attachments=attachments)

    def send_proposals(self, leads: Iterable[BusinessLead], dry_run: bool = True) -> list[str]:
        """Envia propostas apenas para leads aprovados/permitidos."""
        sent_to: list[str] = []
        for lead in leads:
            if not lead.is_contactable:
                continue

            subject = f"{lead.name}: um site profissional para vender mais"
            body = self._proposal_body(lead)
            if dry_run:
                print(f"[DRY RUN] Enviaria proposta para {lead.email}: {subject}")
            else:
                self._send_email(lead.email, subject, body)
            sent_to.append(lead.email)
        return sent_to

    def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Sequence[Path] = (),
    ) -> None:
        if not self.smtp_user or not self.smtp_password:
            raise ValueError("Configure SMTP_USER e SMTP_PASSWORD para enviar e-mails.")

        message = EmailMessage()
        message["From"] = f"{self.sender_name} <{self.smtp_user}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        for attachment in attachments:
            data = attachment.read_bytes()
            message.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=attachment.name,
            )

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(message)

    def _report_body(self, leads: Sequence[BusinessLead]) -> str:
        top_leads = "\n".join(
            f"- {lead.name} | {lead.rating:.1f}⭐ ({lead.review_count} avaliações) | {lead.address} | {lead.maps_url}"
            for lead in leads[:20]
        )
        return textwrap.dedent(
            f"""
            Olá! O agente CEO finalizou uma rodada de prospecção.

            Total de empresas qualificadas: {len(leads)}
            Critério principal: boa avaliação, volume mínimo de avaliações e ausência de site no Google Places.

            Top leads:
            {top_leads or '- Nenhum lead encontrado nesta rodada.'}

            Próximo passo recomendado:
            1. Revisar o CSV anexo.
            2. Completar e-mail/WhatsApp usando fonte autorizada.
            3. Marcar consent_status como approved/opt_in/customer_requested antes de disparar propostas.
            """
        ).strip()

    def _proposal_body(self, lead: BusinessLead) -> str:
        first_name = lead.name.split()[0]
        return textwrap.dedent(
            f"""
            Olá, equipe {first_name}! Tudo bem?

            Encontrei a {lead.name} no Google Maps e vi que vocês já têm uma reputação forte: {lead.rating:.1f} estrelas com {lead.review_count} avaliações. Isso mostra confiança — e um site próprio pode transformar essa confiança em mais pedidos, reservas e contatos todos os dias.

            Um site profissional ajuda a empresa a:
            - aparecer melhor quando o cliente pesquisa no Google;
            - explicar serviços, diferenciais, horários e localização em uma página organizada;
            - receber contatos por WhatsApp, formulário e botões de ação;
            - passar mais credibilidade do que depender só de redes sociais ou Maps;
            - medir visitas e campanhas para vender mais.

            Minha proposta é criar uma landing page moderna para o nicho de {lead.niche}, com visual premium, animações 3D leves, botão de WhatsApp, mapa, prova social e chamada clara para orçamento.

            Se fizer sentido, responda este e-mail com "quero ver um exemplo" que eu preparo uma demonstração personalizada para a {lead.name}.

            Abraços,
            {self.sender_name}
            """
        ).strip()


@dataclass(slots=True)
class SiteSection:
    title: str
    text: str
    cta: str = ""


class DemoSiteAgent:
    """Gera uma demonstração HTML com estética 3D e animações leves."""

    def __init__(self, output_dir: Path = DEMOS_DIR) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_demo(self, lead: BusinessLead) -> Path:
        slug = self._slugify(lead.name)
        path = self.output_dir / f"{slug}.html"
        path.write_text(self._render_html(lead), encoding="utf-8")
        return path

    def _render_html(self, lead: BusinessLead) -> str:
        safe_name = html.escape(lead.name)
        safe_niche = html.escape(lead.niche or "negócio local")
        safe_address = html.escape(lead.address)
        whatsapp = self._whatsapp_link(lead)
        return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_name} | Site demonstrativo</title>
  <style>
    :root {{ color-scheme: dark; --accent: #67e8f9; --gold: #fbbf24; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, Arial, sans-serif; background: radial-gradient(circle at top, #1e3a8a, #020617 58%); color: #fff; overflow-x: hidden; }}
    .orb {{ position: fixed; width: 24rem; height: 24rem; border-radius: 50%; filter: blur(90px); opacity: .45; animation: float 9s ease-in-out infinite; }}
    .orb.one {{ background: #06b6d4; top: -7rem; left: -5rem; }}
    .orb.two {{ background: #f59e0b; right: -7rem; bottom: 5rem; animation-delay: -3s; }}
    main {{ width: min(1120px, 92vw); margin: auto; position: relative; z-index: 1; }}
    header {{ min-height: 90vh; display: grid; grid-template-columns: 1.1fr .9fr; gap: 3rem; align-items: center; }}
    .badge {{ display: inline-flex; gap: .5rem; padding: .55rem .8rem; border: 1px solid rgba(255,255,255,.16); border-radius: 999px; background: rgba(255,255,255,.08); backdrop-filter: blur(16px); }}
    h1 {{ font-size: clamp(2.6rem, 6vw, 6.5rem); line-height: .92; margin: 1.2rem 0; letter-spacing: -.06em; }}
    p {{ color: #cbd5e1; font-size: 1.08rem; line-height: 1.7; }}
    .cta {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 2rem; }}
    a.button {{ color: #00111a; background: linear-gradient(135deg, var(--accent), var(--gold)); border-radius: 1rem; padding: 1rem 1.2rem; font-weight: 800; text-decoration: none; box-shadow: 0 24px 70px rgba(103,232,249,.28); }}
    a.secondary {{ color: #fff; border: 1px solid rgba(255,255,255,.2); background: rgba(255,255,255,.08); }}
    .phone {{ perspective: 1100px; display: grid; place-items: center; }}
    .card3d {{ width: min(360px, 90vw); min-height: 560px; border: 1px solid rgba(255,255,255,.18); border-radius: 2.2rem; background: linear-gradient(145deg, rgba(255,255,255,.18), rgba(255,255,255,.04)); box-shadow: 0 40px 100px rgba(0,0,0,.42); transform: rotateY(-16deg) rotateX(8deg); animation: tilt 7s ease-in-out infinite; padding: 1.2rem; backdrop-filter: blur(22px); }}
    .screen {{ height: 100%; border-radius: 1.5rem; padding: 1.4rem; background: linear-gradient(180deg, #0f172a, #111827); }}
    .mini-hero {{ border-radius: 1.4rem; padding: 1rem; background: radial-gradient(circle at top left, rgba(103,232,249,.4), rgba(251,191,36,.13)); }}
    .stars {{ color: var(--gold); letter-spacing: .12rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 4rem 0; }}
    .feature {{ padding: 1.4rem; border-radius: 1.5rem; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); }}
    footer {{ padding: 4rem 0; color: #94a3b8; }}
    @keyframes float {{ 50% {{ transform: translate3d(2rem, 3rem, 0) scale(1.05); }} }}
    @keyframes tilt {{ 50% {{ transform: rotateY(12deg) rotateX(-4deg) translateY(-18px); }} }}
    @media (max-width: 840px) {{ header, .grid {{ grid-template-columns: 1fr; }} header {{ padding: 4rem 0; }} .card3d {{ transform: none; }} }}
  </style>
</head>
<body>
  <div class="orb one"></div><div class="orb two"></div>
  <main>
    <header>
      <section>
        <span class="badge">⭐ {lead.rating:.1f} no Google • {lead.review_count} avaliações</span>
        <h1>{safe_name}</h1>
        <p>Uma presença digital premium para {safe_niche}: rápida, bonita e feita para converter visitantes em clientes pelo WhatsApp.</p>
        <div class="cta">
          <a class="button" href="{whatsapp}">Chamar no WhatsApp</a>
          <a class="button secondary" href="#diferenciais">Ver diferenciais</a>
        </div>
      </section>
      <section class="phone" aria-label="Mockup 3D do site">
        <div class="card3d"><div class="screen">
          <div class="mini-hero"><div class="stars">★★★★★</div><h2>{safe_name}</h2><p>{safe_address}</p></div>
          <p>Oferta especial, galeria, depoimentos, mapa e formulário em uma experiência moderna.</p>
        </div></div>
      </section>
    </header>
    <section class="grid" id="diferenciais">
      <div class="feature"><h3>Conversão</h3><p>Botões claros para WhatsApp, ligação e orçamento.</p></div>
      <div class="feature"><h3>Credibilidade</h3><p>Prova social, avaliações e informações organizadas.</p></div>
      <div class="feature"><h3>Performance</h3><p>Layout leve com animações 3D sem travar no celular.</p></div>
    </section>
    <footer>Demo gerada automaticamente para apresentação comercial. Personalização final feita após aprovação.</footer>
  </main>
</body>
</html>
"""

    def _whatsapp_link(self, lead: BusinessLead) -> str:
        raw_number = lead.whatsapp or lead.phone
        digits = re.sub(r"\D+", "", raw_number)
        if digits and not digits.startswith("55"):
            digits = f"55{digits}"
        message = html.escape(f"Olá, {lead.name}! Vim pelo site e gostaria de saber mais.")
        return f"https://wa.me/{digits}?text={message}" if digits else "#"

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        return slug or "site-demo"


class ReplyMonitorAgent:
    """Monitora respostas no Gmail/IMAP e gera demo quando o lead demonstra interesse."""

    def __init__(self, imap_host: str, imap_user: str, imap_password: str, demo_agent: DemoSiteAgent) -> None:
        self.imap_host = imap_host
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.demo_agent = demo_agent

    @classmethod
    def from_env(cls, demo_agent: DemoSiteAgent) -> "ReplyMonitorAgent":
        return cls(
            imap_host=os.getenv("IMAP_HOST", "imap.gmail.com"),
            imap_user=os.getenv("IMAP_USER", os.getenv("SMTP_USER", "")),
            imap_password=os.getenv("IMAP_PASSWORD", os.getenv("SMTP_PASSWORD", "")),
            demo_agent=demo_agent,
        )

    def create_demos_for_interested_replies(self, leads: Sequence[BusinessLead]) -> list[Path]:
        if not self.imap_user or not self.imap_password:
            raise ValueError("Configure IMAP_USER e IMAP_PASSWORD para monitorar respostas.")

        leads_by_email = {lead.email.lower(): lead for lead in leads if lead.email}
        generated: list[Path] = []
        with imaplib.IMAP4_SSL(self.imap_host) as mailbox:
            mailbox.login(self.imap_user, self.imap_password)
            mailbox.select("INBOX")
            status, data = mailbox.search(None, "UNSEEN")
            if status != "OK":
                return generated

            for message_id in data[0].split():
                status, message_data = mailbox.fetch(message_id, "(BODY[TEXT] RFC822.HEADER)")
                if status != "OK" or not message_data:
                    continue
                raw = b" ".join(part for part in message_data[0] if isinstance(part, bytes)).decode(
                    "utf-8",
                    errors="ignore",
                )
                sender = self._extract_sender(raw)
                lead = leads_by_email.get(sender.lower())
                if lead and self._is_interested(raw):
                    generated.append(self.demo_agent.create_demo(lead))
        return generated

    def _extract_sender(self, raw_message: str) -> str:
        match = re.search(r"From:.*?<([^>]+)>", raw_message, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"From:\s*([^\s]+@[^\s]+)", raw_message, flags=re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _is_interested(self, text: str) -> bool:
        normalized = text.lower()
        return any(keyword in normalized for keyword in INTEREST_KEYWORDS)


def load_contacts_overlay(path: Path) -> dict[str, dict[str, str]]:
    """Carrega e-mail/WhatsApp/consentimento de uma planilha própria."""
    if not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as file:
        return {row["place_id"]: row for row in csv.DictReader(file) if row.get("place_id")}


def apply_contacts_overlay(leads: list[BusinessLead], overlay: dict[str, dict[str, str]]) -> list[BusinessLead]:
    for lead in leads:
        data = overlay.get(lead.place_id, {})
        lead.email = data.get("email", lead.email)
        lead.whatsapp = data.get("whatsapp", lead.whatsapp)
        lead.consent_status = data.get("consent_status", lead.consent_status)
        lead.notes = data.get("notes", lead.notes)
    return leads


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentes de prospecção Rex Tech")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Buscar leads no Google Places e enviar relatório")
    collect.add_argument("--niches", required=True, help="Nichos separados por vírgula. Ex: restaurante,barbearia")
    collect.add_argument("--cities", required=True, help="Cidades separadas por vírgula. Ex: São Paulo,Rio de Janeiro")
    collect.add_argument("--owner-email", default=os.getenv("OWNER_EMAIL", ""), help="Gmail que receberá o relatório")
    collect.add_argument("--contacts-csv", type=Path, help="CSV próprio com place_id,email,whatsapp,consent_status")
    collect.add_argument("--min-rating", type=float, default=4.5)
    collect.add_argument("--min-reviews", type=int, default=20)
    collect.add_argument("--no-email", action="store_true", help="Salvar relatório sem enviar por e-mail")

    proposals = subparsers.add_parser("send-proposals", help="Enviar propostas para leads aprovados")
    proposals.add_argument("report", type=Path, help="Relatório JSON ou CSV")
    proposals.add_argument("--send", action="store_true", help="Dispara e-mails reais; sem isso roda em dry-run")

    demos = subparsers.add_parser("monitor-replies", help="Criar demos para respostas interessadas")
    demos.add_argument("report", type=Path, help="Relatório JSON ou CSV")

    demo_one = subparsers.add_parser("demo", help="Criar demo HTML para um lead específico do relatório")
    demo_one.add_argument("report", type=Path, help="Relatório JSON ou CSV")
    demo_one.add_argument("--email", help="E-mail do lead")
    demo_one.add_argument("--place-id", help="Place ID do lead")

    return parser


def split_csv_arg(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "collect":
        ceo = GoogleMapsLeadCeoAgent(
            api_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
            min_rating=args.min_rating,
            min_reviews=args.min_reviews,
        )
        leads = ceo.collect_leads(split_csv_arg(args.niches), split_csv_arg(args.cities))
        if args.contacts_csv:
            leads = apply_contacts_overlay(leads, load_contacts_overlay(args.contacts_csv))
        json_path, csv_path = LeadReportStore().save(leads)
        print(f"Relatórios salvos: {json_path} e {csv_path}")
        if not args.no_email:
            if not args.owner_email:
                raise ValueError("Informe --owner-email ou configure OWNER_EMAIL.")
            EmailProposalAgent.from_env().send_report(args.owner_email, leads, [json_path, csv_path])
            print(f"Relatório enviado para {args.owner_email}")

    elif args.command == "send-proposals":
        leads = LeadReportStore.load(args.report)
        sent_to = EmailProposalAgent.from_env().send_proposals(leads, dry_run=not args.send)
        print(f"Propostas elegíveis processadas: {len(sent_to)}")

    elif args.command == "monitor-replies":
        leads = LeadReportStore.load(args.report)
        generated = ReplyMonitorAgent.from_env(DemoSiteAgent()).create_demos_for_interested_replies(leads)
        for path in generated:
            print(f"Demo criada: {path}")
        print(f"Total de demos criadas: {len(generated)}")

    elif args.command == "demo":
        leads = LeadReportStore.load(args.report)
        selected = next(
            (
                lead
                for lead in leads
                if (args.email and lead.email == args.email) or (args.place_id and lead.place_id == args.place_id)
            ),
            None,
        )
        if not selected:
            raise ValueError("Lead não encontrado por --email ou --place-id.")
        print(DemoSiteAgent().create_demo(selected))


if __name__ == "__main__":
    main()
