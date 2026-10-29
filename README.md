# Streamify

Um mini serviço de streaming de trilhas sonoras de games, dividido em três microsserviços Flask.

📖 Explicação completa, passo a passo: [COMO_FUNCIONA.md](COMO_FUNCIONA.md)

| Serviço            | Porta | Endpoints principais |
|--------------------|-------|----------------------|
| `music_service`    | 5001  | `GET /music`, `GET /music/<id>` |
| `playlist_service` | 5002  | `GET/POST /playlists`, `GET /playlists/<id>`, `POST /playlists/<id>/tracks`, `DELETE /playlists/<id>/tracks/<track_id>` |
| `playback_service` | 5003  | `GET /playback/status`, `POST /playback/play` `pause` `resume` `stop` |

Todos expõem `GET /health`.

## Rodando localmente

```bash
docker compose up --build
```

## Testes

```bash
pip install -r requirements-dev.txt
cd music_service && pip install -r requirements.txt && python -m pytest -v
```

(repita para `playlist_service` e `playback_service`)

## Infraestrutura (Terraform)

A pasta `terraform/` cria VPC, subnet pública, internet gateway, security group e uma EC2 na AWS.
O deploy no GitHub Actions só roda manualmente (aba **Actions → Run workflow**) e precisa dos
secrets `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`. Antes de usar no CI, configure o backend S3
em `terraform/main.tf` para o estado não se perder entre execuções.
