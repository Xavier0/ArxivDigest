<p align="center"><img src="./readme_images/banner.png" width=500 /></p>

**ArXiv Digest and Personalized Recommendations using Large Language Models.**

This repo aims to provide a better daily digest for newly published arXiv papers based on your own research interests and natural-language descriptions, using relevancy ratings from GPT or other compatible LLMs.

You can try it out on [Hugging Face](https://huggingface.co/spaces/AutoLLM/ArxivDigest) using your own OpenAI API key.

You can also create a daily subscription pipeline to email you the results.

## 🆕 What's New in Enhanced Version

- **🔧 Custom API Support**: Use SiliconFlow, DeepSeek, or any OpenAI-compatible API
- **🌍 Bilingual Output**: Automatic Chinese and English analysis
- **📧 Enhanced Email**: SMTP support with multi-recipient capability
- **🔬 Multi-Topic Search**: Search across multiple arXiv categories simultaneously
- **🧪 Test Mode**: Quick testing with single paper analysis
- **⚡ Quick Start Tools**: Automated setup and testing scripts
- **🎯 Specialized Configs**: Pre-configured for analog circuit design and optimization

## 📚 Contents

- [What this repo does](#🔍-what-this-repo-does)
  * [Examples](#some-examples)
- [Quick Start](#🚀-quick-start)
- [Usage](#💡-usage)
  * [Running as a github action with custom APIs](#running-as-a-github-action-with-custom-apis-recommended)
  * [Running as a github action using SendGrid](#running-as-a-github-action-using-sendgrid)
  * [Running as a github action with SMTP credentials](#running-as-a-github-action-with-smtp-credentials)
  * [Running from the command line](#running-from-the-command-line)
  * [Running with a user interface](#running-with-a-user-interface)
- [Configuration](#⚙️-configuration)
- [Testing Tools](#🧪-testing-tools)
- [Roadmap](#✅-roadmap)
- [Extending and Contributing](#💁-extending-and-contributing)

## 🔍 What this repo does

Staying up to date on [arXiv](https://arxiv.org) papers can take a considerable amount of time, with on the order of hundreds of new papers each day to filter through. There is an [official daily digest service](https://info.arxiv.org/help/subscribe.html), however large categories like [cs.AI](https://arxiv.org/list/cs.AI/recent) still have 50-100 papers a day. Determining if these papers are relevant and important to you means reading through the title and abstract, which is time-consuming.

This repository offers a method to curate a daily digest, sorted by relevance, using large language models. These models are conditioned based on your personal research interests, which are described in natural language. 

### Enhanced Features:

* **Multi-API Support**: Use OpenAI, SiliconFlow, DeepSeek, or any OpenAI-compatible API
* **Bilingual Analysis**: Get paper analysis in both English and Chinese
* **Multi-Topic Search**: Search across multiple arXiv subjects simultaneously (e.g., Computer Science + Electrical Engineering)
* **Advanced Email**: SendGrid, Gmail SMTP, or custom SMTP with multi-recipient support
* **Test Mode**: Quick testing with single paper to verify configuration
* **Smart Categorization**: Automatic filtering by research areas and detailed analysis based on paper type

### Workflow:

* You modify the configuration file `config.yaml` with arXiv subjects, categories, API settings, and a natural language statement about your interests
* The code pulls abstracts for papers in those categories and ranks relevance (1-10) using your chosen LLM
* Papers get detailed bilingual analysis based on type (circuit design papers get concise summaries, algorithmic papers get detailed explanations)
* The code generates an HTML digest and optionally emails it to multiple recipients

### Testing it out with Hugging Face:

We provide a demo at [https://huggingface.co/spaces/AutoLLM/ArxivDigest](https://huggingface.co/spaces/AutoLLM/ArxivDigest). Simply enter your [OpenAI API key](https://platform.openai.com/account/api-keys) and then fill in the configuration on the right. Note that we do not store your key.

![hfexample](./readme_images/hf_example.png)

### Some examples of results:

#### Enhanced Bilingual Configuration:
- Subjects: Computer Science, Electrical Engineering and Systems Science
- Categories: Artificial Intelligence, Machine Learning, Systems and Control
- Interest: Analog circuit design with ML/AI methods, optimization algorithms
- Output: Bilingual (English + Chinese) detailed analysis

#### Result:
<p align="left"><img src="./readme_images/example_1.png" width=580 /></p>

#### Multi-Topic Finance Configuration:
- Subject/Topic: Quantitative Finance
- Interest: "making lots of money"

#### Result:
<p align="left"><img src="./readme_images/example_2.png" width=580 /></p>

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

1. **Fork and clone the repository**
2. **Set up API key**:
   ```bash
   export CUSTOM_API_KEY='your-siliconflow-or-openai-api-key'
   # Or create a .env file with: CUSTOM_API_KEY=your-api-key
   ```
3. **Run the quick start script**:
   ```bash
   python quick_start.py
   ```
   This will automatically:
   - Check your environment and dependencies
   - Test your API configuration
   - Optionally test SMTP settings
   - Run a full digest generation

### Option 2: Manual Testing

1. **Test API connection**:
   ```bash
   python test_api.py
   ```
2. **Test email configuration** (optional):
   ```bash
   python test_smtp.py
   ```
3. **Check today's papers**:
   ```bash
   python quick_check.py
   ```
4. **Generate digest**:
   ```bash
   python src/action.py --config config.yaml
   ```

## 💡 Usage

### Running as a github action with custom APIs (Recommended)

The enhanced way to get started uses custom APIs like SiliconFlow:

1. Fork the repository
2. Modify `config.yaml` for your research interests
3. Set the following secrets [(under settings, Secrets and variables, repository secrets)](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository):
   - `CUSTOM_API_KEY` From [SiliconFlow](https://siliconflow.cn) or other provider
   - **Email settings** (choose one):
     - **SMTP**: `MAIL_CONNECTION`, `FROM_EMAIL`, `TO_EMAIL`
     - **Gmail**: `MAIL_USERNAME`, `MAIL_PASSWORD`, `FROM_EMAIL`, `TO_EMAIL`
     - **SendGrid**: `SENDGRID_API_KEY`, `FROM_EMAIL`, `TO_EMAIL`
4. Manually trigger the action or wait for scheduled execution

### Running as a github action using SendGrid

1. Fork the repository
2. Modify `config.yaml` and merge the changes into your main branch.
3. Set the following secrets:
   - `OPENAI_API_KEY` From [OpenAI](https://platform.openai.com/account/api-keys)
   - `SENDGRID_API_KEY` From [SendGrid](https://app.SendGrid.com/settings/api_keys)
   - `FROM_EMAIL` This value must match the email you used to create the SendGrid API Key.
   - `TO_EMAIL` (supports multiple recipients: `user1@example.com,user2@example.com`)
4. Manually trigger the action or wait until the scheduled action takes place.

### Running as a github action with SMTP credentials

An enhanced alternative using SMTP:

1. Fork the repository
2. Modify `config.yaml` and merge changes
3. Set the following secrets:
   - `CUSTOM_API_KEY` or `OPENAI_API_KEY`
   - **SMTP Connection String**: `MAIL_CONNECTION=smtp://user:password@server:port`
   - **Or Gmail Credentials**: `MAIL_USERNAME` and `MAIL_PASSWORD`
   - `FROM_EMAIL` and `TO_EMAIL`
4. Trigger manually or wait for scheduled execution

### Running from the command line

Enhanced local setup:

1. Install requirements: `pip install -r requirements.txt`
2. Copy `.env.template` to `.env` and configure your API keys
3. Modify `config.yaml` for your interests
4. **Test your setup**:
   ```bash
   python test_api.py      # Test API connection
   python test_smtp.py     # Test email (optional)
   python quick_check.py   # Check today's papers
   ```
5. **Generate digest**:
   ```bash
   python src/action.py --config config.yaml
   # Or test mode: python src/action.py --config config.yaml --test-mode
   ```
6. Open `digest.html` in your browser

### Running with a user interface

To locally run the UI:

1. Install requirements including `gradio`: `pip install -r requirements.txt gradio`
2. Run `python src/app.py` and go to the local URL
3. Configure API keys in the interface or via `.env` file

> **WARNING:** Never commit your API keys! Always use environment variables or the `.env` file.

## ⚙️ Configuration

### Enhanced config.yaml Options

```yaml
# Multi-topic support
topics:
  - "Computer Science" 
  - "Electrical Engineering and Systems Science"

# Target categories
categories:
  - "Artificial Intelligence"
  - "Machine Learning"
  - "Systems and Control"

# Relevancy threshold (0-10)
threshold: 6

# API Configuration (enhanced)
api_config:
  use_custom_api: true  # false for OpenAI
  api_url: "https://api.siliconflow.cn/v1/chat/completions"
  model_name: "Pro/deepseek-ai/DeepSeek-V3"
  # API key set via CUSTOM_API_KEY environment variable

# Bilingual research interests
interest: |
  Describe your research interests in detail.
  
  **For circuit design papers**: Brief methodology summaries
  **For algorithmic papers**: Detailed theoretical analysis
  
  Output in both English and Chinese.
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# API Configuration (choose one)
CUSTOM_API_KEY=your-custom-api-key    # SiliconFlow, DeepSeek, etc.
OPENAI_API_KEY=your-openai-key        # Traditional OpenAI

# Email Configuration (choose one method)

# Method 1: SMTP Connection String
MAIL_CONNECTION=smtp://user:pass@smtp.gmail.com:587
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient1@example.com,recipient2@example.com

# Method 2: Gmail Credentials
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com  
TO_EMAIL=recipient1@example.com,recipient2@example.com

# Method 3: SendGrid
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=your-verified@email.com
TO_EMAIL=recipient1@example.com,recipient2@example.com
```

## 🧪 Testing Tools

### API Testing
```bash
python test_api.py
```
Tests your API configuration and paper analysis functionality.

### Email Testing  
```bash
python test_smtp.py
```
Tests SMTP configuration with multi-recipient support. Sends either the latest `digest.html` or a test email.

### Paper Analysis
```bash
python quick_check.py
```
Shows today's available papers and categories to help configure your `config.yaml`.

### Complete Testing
```bash
python quick_start.py
```
Comprehensive automated testing of all components.

### Test Mode
```bash
# Test with single paper
python src/action.py --config config.yaml --test-mode

# Or use test configuration
python src/action.py --config test-config.yaml
```

## ✅ Roadmap

- [x] Support personalized paper recommendation using LLM
- [x] Send emails for daily digest
- [x] **Support custom APIs (SiliconFlow, DeepSeek, etc.)**
- [x] **Bilingual output (English + Chinese)**
- [x] **Multi-topic search across arXiv categories**
- [x] **SMTP email support with multi-recipient**
- [x] **Test mode and debugging tools**
- [x] **Specialized configurations for different research areas**
- [ ] Implement ranking factor to prioritize specific authors
- [ ] Support fully open-source models (LLaMA, Vicuna, MPT)
- [ ] Fine-tune models for better paper ranking
- [ ] Web interface with user accounts
- [ ] Integration with more academic databases

## 💁 Extending and Contributing

### Custom API Integration

To add support for new API providers, modify `utils.py`:

```python
def custom_api_completion(prompts, decoding_args, api_config, **kwargs):
    # Add your custom API logic here
    # Return OpenAI-compatible response format
```

### Language Support

To add new languages, modify:
- `relevancy_prompt.txt` - Add language-specific instructions
- `relevancy.py` - Update post-processing for new language fields
- `action.py` - Update HTML generation

### Email Providers

To add new email providers, extend the email sending functions in `action.py`.

### Specialized Domains

Create domain-specific configurations like `config-biology.yaml`, `config-finance.yaml` with appropriate:
- Subject combinations
- Category selections  
- Interest templates
- Output formatting

You are encouraged to modify this code for your needs. If your modifications would help others, please submit a pull request!

See [Advanced Usage](./advanced_usage.md) for detailed step-by-step instructions with screenshots.