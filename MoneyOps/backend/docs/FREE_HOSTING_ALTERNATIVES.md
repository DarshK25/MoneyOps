# Free Hosting & Shared DB (No 30-Day Expiry)

Railway gives limited free credit and can expire. For a **student dev setup** where you want a **shared database** and something that **keeps running** (or is easy to restart), these options are more “always available” and free.

---

## Option 1: Free MySQL in the cloud + run backend locally (recommended for dev)

**Idea:** One shared MySQL in the cloud. Everyone on the team runs the backend (and frontend) **on their own machine**, all pointing to the **same DB**. No expiry, no Railway credits.

### Free MySQL providers (no 30-day trial)

| Provider | What you get | Limits |
|----------|--------------|--------|
| **[db4free.net](https://www.db4free.net)** | Free MySQL 8.0 | 200 MB, must re-register every 6 months (free). |
| **[PlanetScale](https://planetscale.com)** | Free MySQL-compatible (Vitess) | 5 GB, 1 billion row reads/month; DB can “sleep” after 7 days inactivity on free tier. |
| **[Aiven](https://aiven.io)** | Free MySQL (trial then paid) | Check current free tier. |
| **[Neon](https://neon.tech)** | **PostgreSQL** (not MySQL) | 0.5 GB free, no 30-day expiry; would require switching backend to Postgres. |

**Practical choice for MySQL:** **db4free.net** or **PlanetScale** (if you’re OK with possible sleep on free tier).

### Steps (example: db4free.net)

1. Sign up at [db4free.net](https://www.db4free.net) and create a database (e.g. `moneyops`).
2. Note: **host**, **port**, **database name**, **username**, **password**.
3. In your **backend** `application.yml` (or env vars), set:
   - `DB_URL=jdbc:mysql://HOST:PORT/DATABASE?useSSL=false`
   - `DB_USER=...`
   - `DB_PASS=...`
   - `DB_DRIVER=com.mysql.cj.jdbc.Driver`
   - `HIBERNATE_DIALECT=org.hibernate.dialect.MySQLDialect`
   - `JPA_DDL_AUTO=update`
4. Run backend locally: `mvn spring-boot:run`. Tables/columns are created on first run.
5. Share the **same** host, port, DB name, user, password with teammates. They use it in their local env vars; everyone shares one DB.

**No Railway needed.** Data stays in the cloud; backend runs on each dev’s machine.

---

## Option 2: Render (free backend + free Postgres)

**Idea:** Host the **backend** and **database** on [Render](https://render.com). Free tier has limits but **no fixed 30-day expiry**; free Postgres and free web service (spins down after 15 min inactivity, then wakes on request).

- **Backend:** Free Web Service (from GitHub). Spins down when idle; first request may be slow.
- **DB:** Free PostgreSQL. If you stay on MySQL, use **PlanetScale** or **db4free** for DB and only host backend on Render (or run backend locally and only use shared MySQL).

If you’re willing to switch to **PostgreSQL** for the backend, Render gives you one free Postgres DB and one free web service; good for a shared student project.

---

## Option 3: GitHub Student Developer Pack

1. Go to [education.github.com/pack](https://education.github.com/pack).
2. Get the **Student Developer Pack** (with student email).
3. Check current offers: often includes **Railway**, **MongoDB Atlas**, **PlanetScale**, **Neon**, etc. — extra free credit or longer free tiers.
4. Use one of those for a shared DB or backend; read each provider’s terms for expiry.

---

## Option 4: Everything local + one shared cloud DB

- **Backend / Frontend / API Gateway / AI Gateway / Voice:** Everyone runs locally (`mvn spring-boot:run`, `npm run dev`, etc.).
- **Database:** One shared MySQL (db4free.net or PlanetScale). Everyone sets the same `DB_URL`, `DB_USER`, `DB_PASS` in their local env (or in a shared `.env.example` with placeholders; never commit real passwords).

Result: **No hosting cost, no 30-day expiry**, shared data for the whole team. Best for “we’re developing and want to see the same data.”

---

## Quick comparison

| Goal | Suggestion |
|------|------------|
| Shared MySQL, no expiry, minimal setup | **db4free.net** (or PlanetScale) + everyone runs backend locally, same DB env vars. |
| Free hosted backend + DB, OK with Postgres | **Render** (free Postgres + free web service). |
| Extra free credits / longer trials | **GitHub Student Pack** + use listed DB/hosting. |
| Railway from scratch | Use **RAILWAY_FULL_SETUP.md**; be aware of credit/expiry and consider moving DB to db4free/PlanetScale later. |

---

## Summary

- **Tables, columns, data:** Created and updated by your **Spring Boot app** (Hibernate with `JPA_DDL_AUTO=update`) when it connects to **any** MySQL you point it to (Railway, db4free, PlanetScale, etc.).
- **“Runs anytime” + shared DB for students:** Use a **free MySQL** (e.g. db4free.net or PlanetScale) and run the backend **locally** on each machine with the same DB credentials; or use Render + free Postgres if you switch to Postgres.
