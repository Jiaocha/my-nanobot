- Timeouts are configured to prevent hanging requests
- Consider using a firewall to restrict outbound connections if needed

**WhatsApp Bridge:**
- The bridge binds to `127.0.0.1:3001` (localhost only, not accessible from external network)
- Set `bridgeToken` in config to enable shared-secret authentication between Python and Node.js
- Keep authentication data in `~/.nanobot/whatsapp-auth` secure (mode 0700)

### 6. Dependency Security

**Critical**: Keep dependencies updated!

```bash
# Check for vulnerable dependencies
pip install pip-audit
pip-audit

# Update to latest secure versions
pip install --upgrade nanobot-ai
```

For Node.js dependencies (WhatsApp bridge):
```bash
cd bridge
npm audit
npm audit fix
```

**Important Notes:**
- Keep `litellm` updated to the latest version for security fixes
- We've updated `ws` to `>=8.17.1` to fix DoS vulnerability
- Run `pip-audit` or `npm audit` regularly
- Subscribe to security advisories for nanobot and its dependencies

### 7. Production Deployment

For production use:

1. **Isolate the Environment**
   ```bash
   # Run in a container or VM
   docker run --rm -it python:3.11
   pip install nanobot-ai
   ```

2. **Use a Dedicated User**
   ```bash
   sudo useradd -m -s /bin/bash nanobot
   sudo -u nanobot nanobot gateway
   ```

3. **Set Proper Permissions**
   ```bash
   chmod 700 ~/.nanobot
   chmod 600 ~/.nanobot/config.json
   chmod 700 ~/.nanobot/whatsapp-auth
   ```

4. **Enable Logging**
   ```bash
   # Configure log monitoring
   tail -f ~/.nanobot/logs/nanobot.log
   ```

5. **Use Rate Limiting**
   - Configure rate limits on your API providers
   - Monitor usage for anomalies
   - Set spending limits on LLM APIs

6. **Regular Updates**
   ```bash
   # Check for updates weekly
   pip install --upgrade nanobot-ai
   ```

### 8. Development vs Production

**Development:**
- Use separate API keys
- Test with non-sensitive data
- Enable verbose logging
- Use a test Telegram bot

**Production:**
- Use dedicated API keys with spending limits
- Restrict file system access
- Enable audit logging
- Regular security reviews
- Monitor for unusual activity

### 9. Data Privacy

- **Logs may contain sensitive information** - secure log files appropriately
- **LLM providers see your prompts** - review their privacy policies
- **Chat history is stored locally** - protect the `~/.nanobot` directory
- **API keys are in plain text** - use OS keyring for production

### 10. Incident Response

If you suspect a security breach:

1. **Immediately revoke compromised API keys**
2. **Review logs for unauthorized access**
   ```bash
   grep "Access denied" ~/.nanobot/logs/nanobot.log
   ```
3. **Check for unexpected file modifications**
4. **Rotate all credentials**
5. **Update to latest version**
6. **Report the incident** to maintainers

## Security Features

### Built-in Security Controls

✅ **Input Validation**
- Path traversal protection on file operations
- Dangerous command pattern detection
- Input length limits on HTTP requests

✅ **Authentication**
- Allow-list based access control — in `v0.1.4.post3` and earlier empty means allow all; in newer versions empty means deny all (`["*"]` to explicitly allow all)
- Failed authentication attempt logging

✅ **Resource Protection**
- Command execution timeouts (60s default)
- Output truncation (10KB limit)
- HTTP request timeouts (10-30s)

✅ **Secure Communication**
- HTTPS for all external API calls
- TLS for Telegram API
- WhatsApp bridge: localhost-only binding + optional token auth

## Known Limitations

⚠️ **Current Security Limitations:**

1. **No Rate Limiting** - Users can send unlimited messages (add your own if needed)
2. **Plain Text Config** - API keys stored in plain text (use keyring for production)
3. **No Session Management** - No automatic session expiry
4. **Limited Command Filtering** - Only blocks obvious dangerous patterns
5. **No Audit Trail** - Limited security event logging (enhance as needed)

## Security Checklist

Before deploying nanobot:

- [ ] API keys stored securely (not in code)
- [ ] Config file permissions set to 0600
- [ ] `allowFrom` lists configured for all channels
- [ ] Running as non-root user
- [ ] File system permissions properly restricted
- [ ] Dependencies updated to latest secure versions
- [ ] Logs monitored for security events
- [ ] Rate limits configured on API providers
- [ ] Backup and disaster recovery plan in place
- [ ] Security review of custom skills/tools

## Updates

**Last Updated**: 2026-02-03

For the latest security updates and announcements, check:
- GitHub Security Advisories: https://github.com/HKUDS/nanobot/security/advisories
- Release Notes: https://github.com/HKUDS/nanobot/releases

## License

See LICENSE file for details.
