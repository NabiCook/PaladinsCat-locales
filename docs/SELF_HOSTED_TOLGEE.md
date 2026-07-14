# Local Tolgee setup for contributors

This setup runs a private Tolgee instance on your own computer. Nothing needs
to be reachable from the public Internet. PaladinsCat exchanges translation
files with it through the included companion sync helper or manual import/export.

Tolgee's current minimum specification is 2 CPU cores and 4 GB RAM. Docker
Desktop must have at least that much capacity available for a reliable session.

## 1. Create the local files

Create an empty directory and add this `docker-compose.yml`:

```yaml
services:
  tolgee:
    image: tolgee/tolgee:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    env_file:
      - .env
    volumes:
      - tolgee-data:/data

volumes:
  tolgee-data:
```

For a long-lived project, replace `latest` with a tested Tolgee 3.x release tag
before upgrading. The loopback-only port prevents other computers from opening
your Tolgee instance.

Create a `.env` file beside it:

```dotenv
TOLGEE_AUTHENTICATION_ENABLED=true
TOLGEE_AUTHENTICATION_INITIAL_USERNAME=admin
TOLGEE_AUTHENTICATION_INITIAL_PASSWORD=replace-with-a-long-random-password
TOLGEE_AUTHENTICATION_JWT_SECRET=replace-with-a-different-long-random-secret
TOLGEE_AUTHENTICATION_REGISTRATIONS_ALLOWED=false
```

Do not commit `.env`. Use unique random values even though the service is bound
to localhost.

## 2. Start Tolgee

From the directory containing both files:

```powershell
docker compose up -d
docker compose ps
```

Open `http://127.0.0.1:8080` and sign in with the initial account from `.env`.
After the first successful start, remove the initial password from `.env` if
your Tolgee version no longer needs it.

## 3. Create a translation project

1. Create a project named `PaladinsCat Website` or
   `Paladins Game Client`.
2. Select English as the base language.
3. Add the language you intend to translate.
4. Leave public registration disabled.
5. In project developer settings, create a project API key that can view keys
   and translations and edit translations. Keep this key on your computer.
6. Pull a PaladinsCat source bundle as described in
   [CONTRIBUTING_WITH_TOLGEE.md](CONTRIBUTING_WITH_TOLGEE.md).

The two catalogs should be separate Tolgee projects because their keys, release
cycles, and output formats are different.

## 4. Back up or stop the instance

Stop without deleting translations:

```powershell
docker compose stop
```

Start it again:

```powershell
docker compose start
```

Before removing the volume or upgrading Tolgee, export your target-language
files and back up the `tolgee-data` volume. Running `docker compose down` keeps
the named volume; `docker compose down --volumes` permanently deletes it.

## Security rules

- Never publish port 8080 on `0.0.0.0` for this workflow.
- Never send a Tolgee admin token, project API key, `.env`, or data volume to
  PaladinsCat.
- The PaladinsCat contribution token is scoped to catalog submission; it must
  not be placed in Tolgee's administrator settings or shared with anyone.
- Do not enable Tolgee webhooks for PaladinsCat. The sync helper will initiate
  outbound requests, which works without a paid webhook feature or public port.

## References

- [Tolgee Docker installation](https://docs.tolgee.io/platform/self_hosting/running_with_docker)
- [Tolgee supported formats](https://docs.tolgee.io/platform/supported_formats)
- [Tolgee XLIFF 1.2 support](https://docs.tolgee.io/platform/formats/xliff)
