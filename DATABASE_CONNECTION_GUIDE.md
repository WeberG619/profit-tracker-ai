# Finding Your PostgreSQL Connection String on Render

## Steps to Find Your Database URL:

1. **Go to your Render Dashboard**
   - Visit https://dashboard.render.com

2. **Click on your PostgreSQL database** (profit-tracker-db)
   - You should see it in your services list

3. **In the database dashboard, look for "Connections" section**
   - You'll see two types of connection strings:
     - **Internal Database URL** (for services within Render)
     - **External Database URL** (for external connections)

4. **Copy the Internal Database URL**
   - It should look like: `postgresql://profit_tracker_db_user:XXXXX@dpg-XXXXX-a.oregon-postgres.render.com/profit_tracker_db`
   - Click the copy button next to it

5. **Add it to your Web Service Environment Variables:**
   - Go to your profit-tracker-ai service
   - Click on "Environment" in the left sidebar
   - Add a new environment variable:
     - Key: `DATABASE_URL`
     - Value: [paste the Internal Database URL you copied]
   - Click "Save Changes"

## Alternative: Direct Database Connection

If you can't find the connection string in the UI:

1. In your PostgreSQL database dashboard, look for:
   - **Hostname**: Something like `dpg-XXXXX-a.oregon-postgres.render.com`
   - **Port**: Usually `5432`
   - **Database**: `profit_tracker_db` (or similar)
   - **Username**: `profit_tracker_db_user` (or similar)
   - **Password**: (hidden, but available when you first created the database)

2. Construct the URL manually:
   ```
   postgresql://[username]:[password]@[hostname]:[port]/[database]
   ```

## Verify the Connection

After adding the DATABASE_URL:
1. Your service will automatically redeploy
2. Check the /health endpoint again
3. It should show `"database_type":"postgresql"` instead of `"sqlite-memory"`

## Important Notes:
- Use the **Internal** Database URL (not External) for better performance
- The connection string contains your password - keep it secure
- The service will automatically restart after adding the environment variable
