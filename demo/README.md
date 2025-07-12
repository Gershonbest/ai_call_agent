# LiveKit Voice Agent Demo

This demo showcases a complete outbound calling voice agent built with LiveKit Agents. The agent can make outbound calls, engage in natural conversations, and perform actions like transferring calls or booking appointments.

## 🎯 Demo Overview

The voice agent demonstrates:
- **Outbound calling** to leads
- **Natural conversation** with AI-powered responses
- **Function tools** for booking appointments and transferring calls
- **SIP integration** for real phone calls
- **Call recording** and analytics
- **Custom prompts** for specific use cases

## 📋 Prerequisites

### System Requirements
- Python 3.9 or higher
- LiveKit CLI installed
- Access to LiveKit server
- SIP trunk configured (for real phone calls)

### Required Accounts & API Keys
- **LiveKit Account**: For voice agent infrastructure
- **OpenAI API Key**: For AI conversation capabilities
- **SIP Provider**: For making actual phone calls
- **Google Calendar API** (optional): For appointment booking

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Navigate to the demo directory
cd demo

# Copy environment template
cp ../env.example .env

# Edit environment variables
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file with your credentials:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# OpenAI ot Google Configuration
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key

# SIP Configuration (for real phone calls)
SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id

# Optional: Google Calendar for appointment booking
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
```

### 3. Install Dependencies

```bash
# From project root
poetry install

# Or with pip
pip install -r requirements.txt
```

### 4. Run the Demo

#### Option A: Using the Python Script
```bash
# Execute outbound call with JSON configuration
python run_outbound_call.py outbound_call.json

# Or see what command would be executed
python run_outbound_call.py outbound_call.json --dry-run
```

#### Option B: Direct LiveKit CLI
```bash
# Execute the LiveKit dispatch command directly
lk dispatch create --new-room --agent-name outbound-caller --metadata '{"phone_number": "+1234567890", "transfer_to": "+0987654321"}'
```

## 📁 Demo Files Structure

```
demo/
├── README.md                 # This file
├── call_agent.py            # Main voice agent implementation
├── prompt.py                # Custom prompt templates
├── outbound_call.json       # Call configuration
├── run_outbound_call.py     # Execution script
└── KMS/                     # Additional resources
```

## 🤖 Voice Agent Features

### Core Capabilities

#### 1. **Outbound Calling**
- Makes real phone calls using SIP integration
- Handles call connection and disconnection
- Supports call transfer to human agents

#### 2. **AI-Powered Conversations**
- Natural language processing with OpenAI
- Context-aware responses
- Dynamic conversation flow

#### 3. **Function Tools**
- **Transfer Call**: Transfer to human agent
- **End Call**: Gracefully end the conversation
- **Book Appointment**: Schedule meetings
- **Check Availability**: Look up available times
- **Answering Machine Detection**: Handle voicemail

#### 4. **Call Recording**
- Automatic audio recording
- S3 storage integration
- Call analytics and insights

### Custom Prompt System

The agent uses a sophisticated prompt system (`prompt.py`) that includes:

- **Lead Information**: Name, email, registration date, interests
- **Brand Customization**: Company-specific messaging
- **Conversation Flow**: Step-by-step interaction guidelines
- **Tone Guidelines**: Professional yet warm communication style

## ⚙️ Configuration

### Call Configuration (outbound_call.json)

```json
{
  "command": "lk dispatch create",
  "options": {
    "new-room": true,
    "agent-name": "outbound-caller",
    "metadata": {
      "phone_number": "+1234567890",
      "transfer_to": "+0987654321",
      "agent_info": {
        "name": "Adam",
        "brand": "Plus Market"
      },
      "lead_info": {
        "name": "John Doe",
        "email": "john@example.com",
        "registeredon": "15 May, 2024",
        "interest": "Forex Trading"
      }
    }
  }
}
```

### Customizing the Agent

#### 1. **Modify Agent Behavior**
Edit `call_agent.py` to add new function tools:

```python
@function_tool()
async def custom_function(self, ctx: RunContext, parameter: str):
    """Your custom function description"""
    # Your implementation here
    return "Function result"
```

#### 2. **Update Prompts**
Modify `prompt.py` to change conversation style:

```python
def set_instruction(agent_name, brand, name, email, registeredon, interest):
    instruction = f"""
    You are {agent_name}, a virtual assistant for {brand}.
    # Your custom instructions here
    """
    return instruction
```

#### 3. **Add New Call Types**
Create new JSON configurations for different use cases:

```json
{
  "command": "lk dispatch create",
  "options": {
    "new-room": true,
    "agent-name": "appointment-scheduler",
    "metadata": {
      "phone_number": "+1234567890",
      "call_type": "appointment_booking",
      "agent_info": {
        "name": "Sarah",
        "brand": "Medical Clinic"
      }
    }
  }
}
```

## 🧪 Testing the Demo

### 1. **Local Testing**
```bash
# Test with a test phone number
python run_outbound_call.py test_call.json

# Monitor logs
tail -f logs/agent.log
```

### 2. **Dry Run Mode**
```bash
# See what command would be executed
python run_outbound_call.py outbound_call.json --dry-run
```

### 3. **Simulation Mode**
```bash
# Test without making actual calls
export SIMULATION_MODE=true
python run_outbound_call.py outbound_call.json
```

## 📊 Monitoring & Analytics

### Call Logs
The agent logs all activities:
- Call initiation and connection
- Conversation flow
- Function tool usage
- Call completion or transfer

### Recording Analytics
- Call duration and quality metrics
- Conversation sentiment analysis
- Success rate tracking
- Transfer and booking statistics

## 🔧 Troubleshooting

### Common Issues

#### 1. **LiveKit Connection Failed**
```bash
# Check LiveKit credentials
echo $LIVEKIT_URL
echo $LIVEKIT_API_KEY

# Test connection
lk room list
```

#### 2. **SIP Call Not Connecting**
```bash
# Verify SIP trunk configuration
echo $SIP_OUTBOUND_TRUNK_ID

# Check SIP provider status
# Contact your SIP provider for troubleshooting
```

#### 3. **OpenAI API Errors**
```bash
# Verify OpenAI API key
echo $OPENAI_API_KEY

# Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### 4. **Agent Not Responding**
```bash
# Check logs for errors
tail -f logs/agent.log

# Verify prompt configuration
python -c "from prompt import set_instruction; print(set_instruction('test', 'test', 'test', 'test', 'test', 'test'))"
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run_outbound_call.py outbound_call.json
```

## 📈 Advanced Features

### 1. **Multi-Agent Support**
Run multiple agents simultaneously:
```bash
# Agent 1: Sales calls
python run_outbound_call.py sales_agent.json

# Agent 2: Support calls
python run_outbound_call.py support_agent.json
```

### 2. **Custom Integrations**
Add your own integrations:
- CRM systems (Salesforce, HubSpot)
- Calendar systems (Google Calendar, Outlook)
- Payment processors (Stripe, PayPal)
- Analytics platforms (Mixpanel, Amplitude)

### 3. **Advanced Analytics**
- Real-time call monitoring
- Conversation sentiment analysis
- Lead scoring and qualification
- Performance optimization insights

## 🔒 Security Considerations

### API Key Management
- Store API keys securely (use environment variables)
- Rotate keys regularly
- Use least-privilege access

### Call Privacy
- Implement call recording consent
- Secure audio storage
- GDPR compliance for EU calls

### Data Protection
- Encrypt sensitive data
- Implement access controls
- Regular security audits

## 📚 Additional Resources

### Documentation
- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [SIP Integration Guide](https://docs.livekit.io/guides/sip/)

### Community
- [LiveKit Discord](https://discord.gg/livekit)
- [GitHub Issues](https://github.com/livekit/agents/issues)
- [Community Forums](https://community.livekit.io/)

### Support
- Technical support: support@livekit.io
- Documentation: docs.livekit.io
- Community: community.livekit.io

## 🎉 Getting Help

If you encounter issues:

1. **Check the logs**: Look for error messages in the console output
2. **Verify configuration**: Ensure all environment variables are set correctly
3. **Test components**: Verify each service (LiveKit, OpenAI, SIP) individually
4. **Community support**: Ask questions in the LiveKit Discord or GitHub issues
5. **Documentation**: Refer to the official LiveKit documentation

## 📝 License

This demo is provided as-is for educational and development purposes. Please refer to the main project license for usage terms.

---

**Happy calling! 🚀**

For questions or support, reach out to the LiveKit community or check the main project documentation. 