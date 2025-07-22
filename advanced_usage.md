# Advanced Usage

## Quick Start Guide

### 🚀 Automated Setup (Recommended)

The easiest way to get started with the enhanced ArXiv Digest:

1. **Fork the repository** by clicking the fork button at the top of this repository page
2. **Clone your fork** and navigate to the directory
3. **Set up API key**:
   ```bash
   # For custom APIs (SiliconFlow, DeepSeek, etc.)
   export CUSTOM_API_KEY='your-api-key'
   
   # Or for OpenAI
   export OPENAI_API_KEY='your-openai-key'
   ```
4. **Run the automated setup**:
   ```bash
   python quick_start.py
   ```

This script will:
- ✅ Check environment variables
- ✅ Test API connectivity
- ✅ Validate email configuration (if provided)
- ✅ Run a complete digest generation
- ✅ Provide troubleshooting guidance

### 🧪 Manual Testing Steps

If you prefer step-by-step testing:

```bash
# 1. Test API connection
python test_api.py

# 2. Check today's available papers and categories
python quick_check.py

# 3. Test email configuration (optional)
python test_smtp.py

# 4. Generate a test digest
python src/action.py --config config.yaml --test-mode

# 5. Generate full digest
python src/action.py --config config.yaml
```

## Step-by-step instructions for running as a Github action

### Fork the repository

Click the fork button at the top of this repository page, as seen on the below image. This will create your own version of the repository, including your own set of github actions

![fork](./readme_images/fork.png)

### Modify the configuration file

Modify `config.yaml` by cloning the repository and merging your changes. The enhanced version supports:

#### Multi-Topic Configuration
```yaml
# Search multiple arXiv subjects
topics:
  - "Computer Science"
  - "Electrical Engineering and Systems Science"
  - "Mathematics"
```

#### Custom API Configuration
```yaml
api_config:
  use_custom_api: true  # Set to false for OpenAI
  api_url: "https://api.siliconflow.cn/v1/chat/completions"
  model_name: "Pro/deepseek-ai/DeepSeek-V3"
```

#### Bilingual Interest Description
```yaml
interest: |
  **Primary Focus - Analog Circuit Design with ML/AI:**
  1. Machine learning methods for analog circuit design
  2. AI-driven electronic design automation (EDA) tools
  
  **Secondary Focus - Optimization Algorithms:**
  1. Reinforcement learning algorithms
  2. Bayesian optimization methods
  
  **Output Requirements:**
  - For circuit papers: Provide concise methodology summaries
  - For algorithmic papers: Provide detailed theoretical analysis
  - All outputs in both Chinese and English
```

### Create and Fetch your API Keys 

#### Option 1: Custom APIs (Recommended)

**SiliconFlow** (Cost-effective, supports multiple models):
- Visit [SiliconFlow](https://siliconflow.cn)
- Create an account and get your API key
- Supports models like DeepSeek-V3, Qwen, etc.
- Much more cost-effective than OpenAI

**Other Compatible APIs**:
- DeepSeek API
- Moonshot API  
- Any OpenAI-compatible endpoint

#### Option 2: OpenAI API

- Create or fetch your API key for [OpenAI](https://platform.openai.com/account/api-keys). Note: you will need an OpenAI account.
![fork](./readme_images/openai.png)

#### Email Service Setup

**SendGrid** (Original method):
- Create or fetch your API key for [SendGrid](https://app.SendGrid.com/settings/api_keys). You will need a SendGrid account. The free tier will generally suffice. Make sure to [verify your sender identity](https://docs.sendgrid.com/for-developers/sending-email/sender-identity).
   - Sign Up for [SendGrid](https://app.sendgrid.com). Fill in the necessary information, including email, password, and a company name. If you don't have a company, you can use a made-up name.
   - You'll need to verify your email address to activate your account.
   - On your main dashboard, access the Integration Guide under Email API
   - Next, on the "Integrate using our Web API or SMTP Relay"-page, choose the "Web API" option.
   - Choose the language you're planning to use, in this case, select "Python".
   - You'll be prompted to provide a name for your API key. Enter a name and click "Create Key".
   - Copy the API Key that appears for the next step below. You won't be able to view the full key again.

**SMTP (Enhanced method)**:
- **Gmail**: Use your Gmail account with an [application password](https://support.google.com/accounts/answer/185833)
- **Custom SMTP**: Use any SMTP server (Outlook, corporate email, etc.)

### Set the secrets for the github action

Go to the Settings tab on the top of this page, and then the "Actions" menu under "Secrets and variables":

![settings](./readme_images/settings.png)

Create repository secrets for your chosen configuration:

#### For Custom APIs + SMTP (Recommended)
- `CUSTOM_API_KEY` (your SiliconFlow/DeepSeek API key)
- `MAIL_CONNECTION` (SMTP connection string: `smtp://user:pass@server:port`)
- `FROM_EMAIL`
- `TO_EMAIL` (supports multiple: `user1@example.com,user2@example.com`)

#### For Custom APIs + Gmail
- `CUSTOM_API_KEY`
- `MAIL_USERNAME` (your Gmail address)
- `MAIL_PASSWORD` (your app password)
- `FROM_EMAIL`
- `TO_EMAIL`

#### For OpenAI + SendGrid (Original)
- `OPENAI_API_KEY`
- `SENDGRID_API_KEY`
- `FROM_EMAIL`
- `TO_EMAIL`

![secret](./readme_images/secrets.png)

### Enhanced GitHub Action Features

The updated workflow (`.github/workflows/daily_digest.yaml`) includes:

#### Test Mode Support
- Manual trigger with test mode option
- Processes only 1 paper for quick validation
- Uses `test-config.yaml` if available

#### Comprehensive Environment Checking
- Validates API keys
- Checks email configuration completeness
- Provides detailed status reporting

#### Multiple Email Methods
- Automatic detection of email configuration type
- Support for SendGrid, SMTP, and Gmail
- Multi-recipient support

#### Enhanced Artifacts
- Separate artifacts for test and full modes
- Includes both HTML output and data files
- Extended retention periods

### Manually trigger the action, or wait until the scheduled trigger

Go to the actions tab, and then click on "ArXiv Digest Daily" and "Run Workflow". You can choose to run in test mode:

![trigger](./readme_images/trigger.png)

The enhanced workflow allows you to:
- Choose test mode (single paper) or full mode
- See detailed status output in the action logs
- Download artifacts even if email fails

## Enhanced Configuration Options

### Multi-Topic Search

Search across multiple arXiv subjects simultaneously:

```yaml
topics:
  - "Computer Science"
  - "Electrical Engineering and Systems Science"
  - "Physics"
  - "Mathematics"
```

### API Configuration Flexibility

```yaml
api_config:
  use_custom_api: true
  api_url: "https://api.siliconflow.cn/v1/chat/completions"
  model_name: "Pro/deepseek-ai/DeepSeek-V3"
  # Options: "Pro/deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct", etc.
```

### Advanced Email Configuration

#### SMTP Connection Strings
```bash
# Gmail
MAIL_CONNECTION=smtp+starttls://username:password@smtp.gmail.com:587

# Outlook/Hotmail  
MAIL_CONNECTION=smtp+starttls://username:password@smtp-mail.outlook.com:587

# Custom SMTP
MAIL_CONNECTION=smtp://username:password@mail.yourcompany.com:587
```

#### Multi-Recipient Support
```bash
# Multiple formats supported
TO_EMAIL=user1@example.com,user2@example.com,user3@example.com
TO_EMAIL="user1@example.com; user2@example.com; user3@example.com"
TO_EMAIL="user1@example.com user2@example.com user3@example.com"
```

### Test Configurations

Create specialized test configurations:

**test-config.yaml** (for quick testing):
```yaml
topics:
  - "Computer Science"
categories:
  - "Machine Learning"
threshold: 0  # Show all papers in test mode
api_config:
  use_custom_api: true
  api_url: "https://api.siliconflow.cn/v1/chat/completions"
  model_name: "Pro/deepseek-ai/DeepSeek-V3"
interest: |
  Testing configuration - analyze any ML paper found.
```

## Alternative Usage Methods

### Running as a github action with enhanced SMTP

1. Fork the repository
2. Modify `config.yaml` and merge changes
3. Set up SMTP secrets:
   ```
   CUSTOM_API_KEY or OPENAI_API_KEY
   MAIL_CONNECTION=smtp://user:password@server:port
   FROM_EMAIL=your-email@domain.com
   TO_EMAIL=recipient1@example.com,recipient2@example.com
   ```
4. Configure schedule in `.github/workflows/daily_digest.yaml` if needed
5. Trigger manually or wait for scheduled execution

### Running as a github action without emails 

If you do not wish to set up email, the enhanced action will:
- Generate the HTML digest
- Store it as a GitHub artifact  
- Provide detailed status in action logs
- Show paper count and processing statistics

You can access the digest from the GitHub action artifacts:

![artifact](./readme_images/artifact.png)

### Running from the command line with enhanced features

Enhanced local setup process:

1. **Install requirements**: `pip install -r requirements.txt`
2. **Configure environment**:
   ```bash
   # Copy template and edit
   cp .env.template .env
   # Edit .env with your API keys and email settings
   ```
3. **Test your setup**:
   ```bash
   python test_api.py      # Test API connection
   python quick_check.py   # Check available papers
   python test_smtp.py     # Test email (optional)
   ```
4. **Modify configuration**: Edit `config.yaml` for your research interests
5. **Run digest generation**:
   ```bash
   # Test mode (1 paper)
   python src/action.py --config config.yaml --test-mode
   
   # Full mode
   python src/action.py --config config.yaml
   ```
6. **View results**: Open `digest.html` in your browser

### Advanced Testing and Debugging

#### API Testing
```bash
python test_api.py
```
This script:
- Tests basic API connectivity
- Validates paper analysis functionality
- Checks JSON response parsing
- Provides detailed error reporting

#### Email Testing
```bash
python test_smtp.py
```
This script:
- Tests SMTP configuration
- Sends test email or actual digest.html
- Supports multi-recipient testing
- Provides connection diagnostics

#### Paper Analysis
```bash
python quick_check.py
```
This script:
- Shows today's available papers by topic
- Lists all discovered categories
- Helps configure category filters
- Suggests relevant categories for your interests

#### Complete System Test
```bash
python quick_start.py
```
This comprehensive script:
- Checks all environment variables
- Tests API connectivity
- Validates email configuration
- Runs complete digest generation
- Provides guided troubleshooting

### Schedule Customization

To modify the schedule in `.github/workflows/daily_digest.yaml`:

```yaml
# Current: Daily at 1:00 AM UTC  
- cron: '0 1 * * *'

# Weekdays only at 9:00 AM UTC (5:00 PM Beijing)
- cron: '0 9 * * 1-5'

# Twice daily: 9:00 AM and 9:00 PM UTC
- cron: '0 9,21 * * *'
```

### Performance and Cost Optimization

#### API Cost Management
- Use custom APIs (SiliconFlow) for 10-50x cost savings vs OpenAI
- Adjust `threshold` to filter papers (higher = fewer papers analyzed)
- Use test mode during configuration

#### Processing Optimization
- Configure `num_paper_in_prompt` in `relevancy.py` (default: 8)
- Adjust `max_tokens` for longer/shorter analyses
- Use specific categories instead of broad topics

#### Email Optimization
- Use SMTP instead of SendGrid to avoid per-email costs
- Configure multiple recipients in single `TO_EMAIL` variable
- Set up digest.html artifact as backup delivery method

## Troubleshooting

### Common API Issues

**SiliconFlow API Errors**:
```bash
# Test connection
python test_api.py

# Check API key format
echo $CUSTOM_API_KEY | cut -c1-10  # Should show first 10 chars
```

**OpenAI API Errors**:
- Verify API key is active and has credits
- Check rate limits if getting 429 errors
- Use newer models like `gpt-3.5-turbo-16k` for longer contexts

### Email Configuration Issues

**SMTP Connection Failures**:
```bash
# Test SMTP
python test_smtp.py

# For Gmail, ensure you have:
# 1. 2-factor authentication enabled
# 2. App password generated (not regular password)
# 3. "Less secure app access" disabled (use app password)
```

**Multi-Recipient Problems**:
- Verify email address format: `user@domain.com`
- Check for valid separators: `,` `;` or space
- Test with single recipient first

### GitHub Action Issues

**Environment Variable Problems**:
- Check secret names match exactly (case-sensitive)
- Verify secrets are set at repository level, not environment level
- Use action logs to see which variables are detected

**Workflow Permissions**:
- Ensure Actions are enabled in repository settings
- Check workflow file syntax with YAML validator
- Verify branch protection rules don't block automated commits

### Paper Processing Issues

**No Papers Found**:
```bash
# Check available papers and categories
python quick_check.py

# Use empty categories list to see all papers
categories: []

# Lower threshold to see more papers
threshold: 0
```

**Relevancy Scoring Problems**:
- Adjust `interest` description to be more specific
- Check if papers match your specified categories
- Review `relevancy_prompt.txt` for prompt engineering

For additional support, check the repository issues or create a new issue with your specific error messages and configuration.