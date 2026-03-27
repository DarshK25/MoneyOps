# Railway MySQL Setup

## 1. Get credentials

- **Railway** → your project → **Database** → **Connect** → **Credentials**
- Note: **Host**, **Port**, **Username**, **Password**, **Database** (usually `railway`).

## 2. Set environment variables

**Option A – Railway (recommended)**  
In Railway → your **Backend service** → **Variables**:

| Variable | Value |
|----------|--------|
| `DB_URL` | `jdbc:mysql://YOUR_HOST:YOUR_PORT/railway?useSSL=false` |
| `DB_USER` | `root` |
| `DB_PASS` | *(paste from Railway Credentials; then regenerate and update)* |
| `DB_DRIVER` | `com.mysql.cj.jdbc.Driver` |
| `HIBERNATE_DIALECT` | `org.hibernate.dialect.MySQLDialect` |
| `JPA_DDL_AUTO` | `update` |

Replace `YOUR_HOST` and `YOUR_PORT` with the values from **Connect** (e.g. `mainline.proxy.rlwy.net`, `52945`).

**Option B – Local run**  
Export in terminal or use a `.env` file (see `.env.example`):

```bash
export DB_URL="jdbc:mysql://HOST:PORT/railway?useSSL=false"
export DB_USER=root
export DB_PASS=your_password
export DB_DRIVER=com.mysql.cj.jdbc.Driver
export HIBERNATE_DIALECT=org.hibernate.dialect.MySQLDialect
```

## 3. SSL

- If you get an SSL error, use `useSSL=false` in `DB_URL` (as above).
- If Railway requires SSL, try: `...?useSSL=true&requireSSL=true`.

## 4. Run

```bash
mvn clean install
mvn spring-boot:run
```

Success: log line **`HikariPool-1 - Start completed.`**

## 5. Share with team

Share only **Host**, **Port**, **Database name**, **Username**, and tell them to use their own **Password** (or a shared one from Railway Variables).  
Never commit passwords to Git; use env vars only.
