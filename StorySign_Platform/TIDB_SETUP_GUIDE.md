# TiDB Cloud Integration Guide for StorySign

This guide will help you integrate your StorySign ASL platform with TiDB Cloud database.

## Overview

Your StorySign backend is already architected to work with TiDB. You just need to:

1. Update configuration with TiDB connection details
2. Install database drivers
3. Run database migrations
4. Test the connection

## Prerequisites

- TiDB Cloud cluster created and running
- Python environment with StorySign dependencies
- Access to your TiDB Cloud dashboard

## Step 1: TiDB Cloud Connection Details

From your TiDB Cloud dashboard, you should have:

- **Host:** `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`
- **Port:** `4000`
- **Database:** `storysign`
- **Username:** `2aT5133t45tARUN.root`
- **Password:** `ek1FdpnVe3LDPcns`

## Step 2: Configuration Update ✅

The `backend/config.yaml` file has been updated with your TiDB Cloud connection details:

```yaml
database:
  host: "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
  port: 4000
  database: "storysign"
  username: "2aT5133t45tARUN.root"
  password: "ek1FdpnVe3LDPcns"
  ssl_disabled: false # SSL enabled for TiDB Cloud
  echo_queries: true # For debugging (set to false in production)
```

## Step 3: Install Database Dependencies

Run the installation script to install required MySQL drivers:

```bash
cd backend
./install_tidb_deps.sh
```

Or install manually:

```bash
pip install sqlalchemy[asyncio]>=2.0.0
pip install asyncmy>=0.2.9
pip install pymysql>=1.1.0
pip install mysql-connector-python>=8.0.0
```

## Step 4: Run Database Migrations

Create all necessary tables in your TiDB database:

```bash
cd backend
python run_migrations.py
```

This will create tables for:

- User Management (users, user_profiles, user_sessions)
- Progress Tracking (practice_sessions, sentence_attempts, user_progress)
- Content Management (stories, lessons, vocabulary)
- Collaborative Features (shared_sessions, collaboration_invites)
- Plugin System (plugins, plugin_configs, plugin_permissions)

## Step 5: Test Connection

Verify everything is working:

```bash
cd backend
python test_tidb_connection.py
```

This will:

- Test basic database connectivity
- Verify all tables were created
- Run sample operations to ensure everything works

## Alternative: Manual Migration

If you prefer to run migrations individually:

```bash
cd backend
python -m migrations.create_user_tables
python -m migrations.create_progress_tables
python -m migrations.create_content_tables
python -m migrations.create_collaborative_tables
python -m migrations.create_plugin_tables
```

## Verification

After successful setup, you should see these tables in your TiDB Cloud dashboard:

### User Management

- `users` - User accounts and authentication
- `user_profiles` - User preferences and settings
- `user_sessions` - Active user sessions

### Progress Tracking

- `practice_sessions` - ASL practice sessions
- `sentence_attempts` - Individual sentence practice attempts
- `user_progress` - Learning progress and achievements

### Content Management

- `stories` - ASL stories and content
- `lessons` - Structured learning lessons
- `vocabulary` - ASL vocabulary items

### Collaborative Features

- `shared_sessions` - Collaborative practice sessions
- `collaboration_invites` - Session invitations

### Plugin System

- `plugins` - Installed plugins
- `plugin_configs` - Plugin configurations
- `plugin_permissions` - Plugin security settings

## Security Notes

- SSL is enabled for TiDB Cloud connections
- Database credentials are stored in config.yaml (consider using environment variables in production)
- All tables use proper foreign key constraints and indexes
- User passwords are hashed using bcrypt

## Troubleshooting

### Connection Issues

- Verify TiDB Cloud cluster is running
- Check firewall settings allow connections from your IP
- Ensure credentials are correct

### Migration Issues

- Check database user has CREATE TABLE permissions
- Verify database name exists in TiDB Cloud
- Review migration logs for specific errors

### Performance

- TiDB Cloud automatically handles scaling
- Connection pooling is configured for optimal performance
- Indexes are created for common query patterns

## Next Steps

Once TiDB integration is complete:

1. **Start your backend server:**

   ```bash
   cd backend
   python main.py
   ```

2. **Test API endpoints** that use database features:

   - User registration/login
   - Practice session tracking
   - Progress analytics

3. **Monitor performance** in TiDB Cloud dashboard

4. **Set up backups** and monitoring as needed

## Production Considerations

For production deployment:

1. **Environment Variables:** Move database credentials to environment variables
2. **SSL Certificates:** Configure proper SSL certificates if needed
3. **Connection Limits:** Adjust pool sizes based on expected load
4. **Monitoring:** Set up TiDB Cloud monitoring and alerts
5. **Backups:** Configure automated backups
6. **Security:** Review and harden database permissions

Your StorySign platform is now ready to use TiDB Cloud for persistent data storage!
