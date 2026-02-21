# Railway: Full Setup From Scratch (Forked Repo)

Use this when you start a **new Railway project** and connect your **forked** GitHub repo. Tables, columns, and data are created automatically when the backend runs with MySQL (Hibernate/JPA).

---

## Prerequisites

- GitHub account with your **fork** of the project (Railway can only use repos you have access to).
- Railway account at [railway.app](https://railway.app).

---

## Step 1: Create a new project

1. Go to [railway.app](https://railway.app) → **Dashboard**.
2. Click **New Project**.
3. You’ll see: “What do you want to deploy?” with options like **Deploy from GitHub repo**, **Empty Project**, etc.

---

## Step 2: Add MySQL (database)

1. In the new project, click **+ New** → **Database** → **Add MySQL** (or **MySQL** plugin).
2. Wait until the MySQL service is provisioned (you’ll see a card for it).
3. Click the **MySQL** card.
4. Open **Variables** or **Connect** and note:
   - **Host** (e.g. `xxx.proxy.rlwy.net`)
   - **Port** (e.g. `12345`)
   - **User** (usually `root`)
   - **Password** (copy it; you’ll use it in the backend)
   - **Database** (often `railway`).
5. Optional: under **Connect**, copy the **Connection URL** or the JDBC-style URL. You’ll build:  
   `jdbc:mysql://HOST:PORT/railway?useSSL=false`

You now have one service: **MySQL**. Tables and columns don’t exist yet; they are created when the backend starts with `JPA_DDL_AUTO=update` and connects to this DB.

---

## Step 3: Add the Backend service (from your forked repo)

1. In the **same project**, click **+ New** → **GitHub Repo** (or **Deploy from GitHub repo**).
2. If asked to connect GitHub:
   - Click **Configure GitHub App** or **Connect GitHub**.
   - Authorize Railway and select your GitHub account (or org).
   - Choose **Only select repositories** and pick your **fork** of the MoneyOps repo.
   - Install / Authorize.
3. Select your **forked repo** from the list (e.g. `YOUR_USERNAME/MoneyOps` or whatever the repo name is).
4. Railway will add a new service and start a deploy. **Don’t rely on the first deploy yet** — you must set the **root directory** and **env vars**.

---

## Step 4: Set Backend root directory (monorepo)

Your repo layout is likely:

```
repo-root/
  MoneyOps/
    backend/     <-- pom.xml is here
    Frontend/
    api-gateway/
    ...
```

1. Click the **backend service** card (the one that was just created from the repo).
2. Go to **Settings** (or the service name → Settings).
3. Find **Root Directory** / **Build Path** / **Monorepo** (wording may vary).
4. Set it to the folder that contains `pom.xml`:
   - If the repo root is the repo root: `MoneyOps/backend`
   - If the repo root is already `MoneyOps`: `backend`
5. Save. Railway will redeploy.

---

## Step 5: Connect Backend to MySQL (env vars)

1. Stay on the **backend service** (not the MySQL card).
2. Open **Variables**.
3. Add variables. You can **reference the MySQL plugin** so Railway fills in host/port/user/password:

   | Variable | Value |
   |----------|--------|
   | `DB_URL` | `jdbc:mysql://${{MySQL.MYSQL_HOST}}:${{MySQL.MYSQL_PORT}}/${{MySQL.MYSQL_DATABASE}}?useSSL=false` |
   | `DB_USER` | `${{MySQL.MYSQL_USER}}` |
   | `DB_PASS` | `${{MySQL.MYSQL_PASSWORD}}` |
   | `DB_DRIVER` | `com.mysql.cj.jdbc.Driver` |
   | `HIBERNATE_DIALECT` | `org.hibernate.dialect.MySQLDialect` |
   | `JPA_DDL_AUTO` | `update` |

   If Railway uses different reference names (e.g. `MySQL.MYSQL_URL`), use **Variables** on the MySQL service to see the exact variable names, or paste the values manually:

   | Variable | Example value |
   |----------|----------------|
   | `DB_URL` | `jdbc:mysql://mainline.proxy.rlwy.net:52945/railway?useSSL=false` |
   | `DB_USER` | `root` |
   | `DB_PASS` | *(paste from MySQL → Variables / Credentials)* |
   | `DB_DRIVER` | `com.mysql.cj.jdbc.Driver` |
   | `HIBERNATE_DIALECT` | `org.hibernate.dialect.MySQLDialect` |
   | `JPA_DDL_AUTO` | `update` |

4. Save. Railway will redeploy the backend.

---

## Step 6: Build and start commands (Backend)

1. In the **backend service** → **Settings**.
2. Set **Build Command** (if needed), e.g. `mvn clean install -DskipTests` or leave default.
3. Set **Start Command**, e.g. `mvn spring-boot:run` or `java -jar target/moneyops-backend-*.jar` (if you build a JAR in the build step).
4. Set **Watch Paths** to `MoneyOps/backend` (or `backend`) so only backend changes trigger deploys.

Save and let it redeploy.

---

## Step 7: Verify connection and tables

1. In the backend service, open **Deployments** → latest deployment → **View Logs**.
2. Look for: **`HikariPool-1 - Start completed.`** → backend is connected to MySQL.
3. Tables and columns are created by Hibernate on first run (`JPA_DDL_AUTO=update`). You don’t create them by hand.
4. To inspect data: MySQL service → **Data** or **Connect** → use a MySQL client (e.g. MySQL Workbench, DBeaver) with the same host, port, user, password, database.

---

## Step 8: (Optional) Frontend and other services

- **Frontend (Vite/React):** Add another service: **+ New** → **GitHub Repo** → same repo → set **Root Directory** to `MoneyOps/Frontend` (or `Frontend`). Set build command (e.g. `npm ci && npm run build`) and start (e.g. `npm run preview` or a static server). Add env vars if needed (e.g. `VITE_API_URL` pointing to your backend URL).
- **API Gateway / AI Gateway / Voice:** Same idea: one service per app, each with its own root directory and env vars. Backend URL for others would be the Railway backend service URL (e.g. `https://your-backend.up.railway.app`).

---

## Summary

| What | Where |
|------|--------|
| **MySQL** | + New → Database → MySQL. Tables/columns created when backend runs. |
| **Backend** | + New → GitHub Repo → your fork. Root directory = `MoneyOps/backend` (or `backend`). |
| **Env vars** | Backend service → Variables: `DB_URL`, `DB_USER`, `DB_PASS`, `DB_DRIVER`, `HIBERNATE_DIALECT`, `JPA_DDL_AUTO`. |
| **Data** | Use MySQL → Connect / Data or a DB client; same credentials for all team members. |

Share with the team: **MySQL host, port, database, user, password** (from Railway MySQL service). Everyone uses the same DB; backend creates/updates schema on start.
