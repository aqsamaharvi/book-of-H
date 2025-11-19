# CI/CD Deployment Setup Guide

This guide will help you set up automatic deployment to your EC2 instance using GitHub Actions.

## Prerequisites

- EC2 instance with SSH access
- Git installed on EC2
- Python 3 installed on EC2
- Nginx configured as reverse proxy (optional but recommended)

## Setup Instructions

### 1. Set up the FastAPI Service on EC2

SSH into your EC2 instance and run:

```bash
# Navigate to home directory
cd ~

# Clone your repository (if not already done)
git clone https://github.com/aqsamaharvi/book-of-H.git
cd book-of-H

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the systemd service file
sudo cp fastapi.service /etc/systemd/system/

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi

# Check service status
sudo systemctl status fastapi
```

### 2. Configure GitHub Secrets

Go to your GitHub repository settings and add these secrets:

**Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

1. **EC2_SSH_PRIVATE_KEY**
   - Content: Your EC2 private key (.pem file content)
   - Open your `Book-Of-H-key.pem` file and copy the entire content
   - ⚠️ Make sure to include the BEGIN and END lines

2. **EC2_HOST**
   - Content: Your EC2 public IP address or domain name
   - Example: `ec2-XX-XXX-XXX-XXX.compute-1.amazonaws.com`
   - Or: `12.34.56.78`

3. **EC2_USER**
   - Content: `ec2-user`
   - (or `ubuntu` if using Ubuntu AMI)

### 3. Give ec2-user sudo permissions for systemctl

On your EC2 instance, run:

```bash
sudo visudo
```

Add this line at the end:

```
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart fastapi, /bin/systemctl status fastapi
```

Save and exit (Ctrl+X, then Y, then Enter).

### 4. Configure Nginx (Optional but Recommended)

Create an Nginx configuration for your FastAPI app:

```bash
sudo nano /etc/nginx/sites-available/fastapi
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Test the Deployment

1. Make a small change to your `main.py`:

```python
@app.get("/", tags=["root"])
async def read_root():
    """Return a simple Hello World message."""
    return {"message": "Hello World - Auto Deployed!"}
```

2. Commit and push to main:

```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

3. Check GitHub Actions:
   - Go to your repository on GitHub
   - Click on "Actions" tab
   - Watch your deployment workflow run

4. Verify deployment:
   - Visit your EC2 instance IP: `http://YOUR_EC2_IP:8000`
   - Or if using Nginx: `http://YOUR_EC2_IP`
   - You should see the updated message

## Troubleshooting

### Check GitHub Actions logs
- Go to Actions tab in your repository
- Click on the failed workflow
- Review the logs

### Check FastAPI service on EC2
```bash
sudo systemctl status fastapi
sudo journalctl -u fastapi -n 50
```

### Check Nginx logs (if using)
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Manual restart
```bash
sudo systemctl restart fastapi
sudo systemctl restart nginx
```

## Security Recommendations

1. **Use security groups**: Restrict SSH access to your IP only
2. **Use SSL/TLS**: Set up HTTPS with Let's Encrypt
3. **Keep secrets safe**: Never commit your .pem files or secrets to Git
4. **Regular updates**: Keep your EC2 instance and packages updated

## Next Steps

- Set up environment variables for production settings
- Configure SSL/TLS with Let's Encrypt
- Set up monitoring and logging
- Add health check endpoints
- Configure database connections (if needed)
