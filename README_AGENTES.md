# Agentes de prospecção Rex Tech

Este projeto agora inclui uma base de agentes para encontrar empresas brasileiras bem avaliadas no Google Maps/Google Places que **não têm site**, gerar relatórios, enviar propostas por e-mail e criar uma demonstração de site 3D quando o lead responder com interesse.

## Arquitetura

- **GoogleMapsLeadCeoAgent**: agente líder/CEO. Consulta a API oficial Google Places Text Search, filtra empresas sem `websiteUri`, com nota mínima e número mínimo de avaliações.
- **LeadReportStore**: salva o relatório em JSON e CSV dentro de `reports/`.
- **EmailProposalAgent**: envia o relatório para o Gmail do dono e dispara propostas apenas para leads marcados como `approved`, `opt_in` ou `customer_requested`.
- **ReplyMonitorAgent**: monitora respostas não lidas via IMAP e identifica mensagens de interesse como “quero”, “exemplo”, “proposta”, “valor” e similares.
- **DemoSiteAgent**: cria um HTML demonstrativo em `generated_sites/` com visual premium, animação 3D, CTA e botão de WhatsApp.

## Importante sobre dados e conformidade

A API oficial do Google Places retorna dados como nome, endereço, telefone, avaliação, link do Maps e site, mas **não retorna e-mail nem WhatsApp**. Por isso, e-mail/WhatsApp precisam ser adicionados por uma fonte própria/autorizada, por CRM ou por uma planilha de enriquecimento compatível com LGPD, termos de uso e boas práticas anti-spam.

O envio automático de propostas é bloqueado por padrão: o comando roda em `dry-run` se você não usar `--send`, e mesmo com `--send` ele só envia para leads com `consent_status` aprovado.

## Variáveis de ambiente

```bash
export GOOGLE_MAPS_API_KEY="sua-chave-google-maps"
export OWNER_EMAIL="seu-gmail@gmail.com"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="465"
export SMTP_USER="seu-gmail@gmail.com"
export SMTP_PASSWORD="senha-de-app-ou-credencial-smtp"
export IMAP_HOST="imap.gmail.com"
export IMAP_USER="seu-gmail@gmail.com"
export IMAP_PASSWORD="senha-de-app-ou-credencial-imap"
export SENDER_NAME="Rex Tech"
```

## Fluxo recomendado

### 1. Buscar empresas e salvar relatório

```bash
python lead_agents.py collect \
  --niches "restaurante,barbearia,clínica estética" \
  --cities "São Paulo,Rio de Janeiro,Belo Horizonte" \
  --owner-email "seu-gmail@gmail.com"
```

Para apenas salvar relatório sem enviar e-mail:

```bash
python lead_agents.py collect \
  --niches "restaurante" \
  --cities "São Paulo" \
  --no-email
```

### 2. Completar contatos e aprovar envio

Crie/edite uma planilha CSV com os campos abaixo e use `place_id` para cruzar com o relatório:

```csv
place_id,email,whatsapp,consent_status,notes
ChIJ...,lead@empresa.com.br,11999999999,approved,Contato validado em fonte própria
```

Valores aceitos para envio:

- `approved`
- `opt_in`
- `customer_requested`

### 3. Enviar propostas

Dry-run, sem envio real:

```bash
python lead_agents.py send-proposals reports/leads-YYYYMMDD-HHMMSS.csv
```

Envio real para leads aprovados:

```bash
python lead_agents.py send-proposals reports/leads-YYYYMMDD-HHMMSS.csv --send
```

### 4. Criar site demonstrativo quando houver resposta interessada

Monitorar respostas não lidas e gerar demos automaticamente:

```bash
python lead_agents.py monitor-replies reports/leads-YYYYMMDD-HHMMSS.csv
```

Criar demo manualmente para um lead específico:

```bash
python lead_agents.py demo reports/leads-YYYYMMDD-HHMMSS.csv --place-id "ChIJ..."
```

O HTML será salvo em `generated_sites/`.
