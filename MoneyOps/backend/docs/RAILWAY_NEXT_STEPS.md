# Railway: Where Is the Backend Service? (Step-by-Step)

You already have a **MySQL database** on Railway. The **backend service** is the app that runs your Spring Boot code and uses that database. On Railway it’s a **separate service** from the database.

---

## What you see on Railway

1. Go to [railway.app](https://railway.app) and log in.
2. Open your project (e.g. **blissful-passion**).
3. On the project dashboard you see **cards** (tiles). Each card is one **service**:
   - **One card = MySQL** (Database) — you already have this. Click it to see Connect, Credentials, Variables, etc.
   - **Another card = your backend (Spring Boot)** — this might not exist yet. If you only see one card (the database), you need to add a backend service.

So: **“Backend service” = the service that runs your Java app**, not the database. If you don’t see it, create it (below).

---

## Option A: You already have a “Backend” or “API” service

1. On the project page, click the **service card** that is your app (e.g. “Backend”, “moneyops-backend”, “API” — not the MySQL card).
2. In the top tabs, click **Variables** (or **Settings** → Variables).
3. Click **+ New Variable** (or **Add variable**) and add these **one by one** (name = left, value = right):

   | Name | Value |
   |------|--------|
   | `DB_URL` | `jdbc:mysql://mainline.proxy.rlwy.net:52945/railway?useSSL=false` |
   | `DB_USER` | `root` |
   | `DB_PASS` | `FbyZjbEtyGIAIBUZTzVwRKvBVMZkwnhd` |
   | `DB_DRIVER` | `com.mysql.cj.jdbc.Driver` |
   | `HIBERNATE_DIALECT` | `org.hibernate.dialect.MySQLDialect` |
   | `JPA_DDL_AUTO` | `update` |

4. Save. Railway will redeploy the service with the new variables. After deploy, check logs for `HikariPool-1 - Start completed.`

---

## Option B: You only have the MySQL card (no backend service yet)

You need to **add a new service** that will run your backend code.

### 1. Create a new service

- On the project page, click **+ New** (or **Add service**).
- Choose **Empty Service** (or **GitHub repo** if your backend code is already on GitHub).

### 2. Name it

- Click the new service card → **Settings** (or the name).
- Set name to e.g. **backend** or **moneyops-backend**. This is your “backend service”.

### 3. Connect your code (pick one)

- **If you use GitHub:**  
  **Settings** → **Connect Repo** → select the repo and the folder that contains `pom.xml` (e.g. `MoneyOps/backend` or the root if the repo is only the backend). Railway will build and run it.

- **If you deploy manually (CLI / Docker):**  
  Configure build and start commands in **Settings** so that the service runs your Spring Boot app (e.g. `mvn spring-boot:run` or run the built JAR).

### 4. Add the database variables to this service

- Stay on **this backend service** (not the MySQL card).
- Open **Variables**.
- Add the same variables as in the table in Option A (DB_URL, DB_USER, DB_PASS, DB_DRIVER, HIBERNATE_DIALECT, JPA_DDL_AUTO).

### 5. (Optional) Link DB for reference

- In the backend service, **Variables** → **+ New Variable**.
- Name: e.g. `MYSQL_URL` (or whatever your docs say).
- Value: `${{ MySQL.MYSQL_URL }}` (this references Railway’s MySQL service).  
  Your Spring Boot app uses **DB_URL** etc.; this link is only if you want Railway to inject the raw MySQL URL for something else.

### 6. Deploy and check

- Trigger a deploy (push to GitHub or “Redeploy” in Railway).
- Open **Deployments** → latest → **View Logs**. You should see `HikariPool-1 - Start completed.` if the backend is connecting to MySQL.

---

## Summary

- **Database (MySQL)** = one service; you already have it.
- **Backend service** = the service that runs your Spring Boot app; it might be a second card or you create it with **+ New**.
- **What you need to do:**  
  Open the **backend service** → **Variables** → add the 6 variables from the table (or from `env.mysql.local.txt`).  
  Then redeploy and check logs for `HikariPool-1 - Start completed.`

---

## Security (important)

The password in `env.mysql.local.txt` was pasted in chat. After you’ve set it once:

1. In Railway, open **MySQL** (database) → **Variables** (or **Credentials**).
2. **Regenerate** the database password.
3. Update **DB_PASS** in your **backend service** Variables with the new password.
4. For local use, update `env.mysql.local.txt` with the new password and keep that file out of Git (it’s already in `.gitignore`).
