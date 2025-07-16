# Professional Wallpaper Bot

A professional-grade Telegram bot that automatically downloads and sends high-quality mobile wallpapers to the channel from multiple sources including Unsplash, Pexels, and Wallhaven.

## 🏗️ Architecture

This project follows **Clean Architecture** principles:

```
src/
├── domain/           # Core business logic
│   ├── entities.py   # Domain entities
│   └── interfaces.py # Abstract interfaces
├── application/      # Use cases and business rules
│   └── use_cases.py  # Application use cases
├── infrastructure/   # External services implementation
│   ├── services.py   # Service implementations
│   ├── storage_service.py
│   ├── telegram_service.py
│   ├── image_downloader.py
│   └── wallpaper_repositories.py
├── presentation/     # Bot commands and handlers
│   └── bot_handlers.py
├── config.py         # Configuration management
└── main.py          # Application entry point
```

## ✨ Features

### Core Features
- 📱 **Mobile-optimized wallpapers** (portrait orientation, minimum 1920px height)
- 🔄 **Automatic source rotation** between Pexels, Unsplash, and Wallhaven
- 🚫 **Duplicate prevention** using image hashing
- ⏰ **Scheduled posting** with configurable intervals
- 📊 **Comprehensive logging** and statistics
- 🔒 **Admin-only access** with secure authentication

### New Professional Features
- 🎯 **Clean Architecture** with separation of concerns
- 📈 **Advanced statistics** with daily tracking
- � **Full admin control** with comprehensive commands
- 🔄 **Automatic scheduling** with proper timing control
- 🎨 **Filtered categories** (no people/girls content)
- 🐳 **Docker support** for easy deployment
- 🔧 **Environment-based configuration**
- 🛡️ **Error handling** and recovery mechanisms

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/bilolkobilov/Wallpaper-Telegram-Bot.git
cd telegram-wallpaper-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run the bot
```bash
python run.py
```

## 🔧 Configuration

### Required Environment Variables
```env
BOT_TOKEN=your_telegram_bot_token_here
CHANNEL_ID=your_channel_id_here
ADMIN_USER_ID=your_admin_user_id_here
```

### API Keys (at least one required)
```env
PEXELS_API_KEY=your_pexels_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
WALLHAVEN_API_KEY=your_wallhaven_api_key_here
```

### Optional Configuration
```env
WALLPAPERS_PER_BATCH=          # Number of wallpapers per batch
BATCH_INTERVAL_HOURS=          # Hours between batches
SEND_DELAY_SECONDS=            # Delay between individual sends
MAX_RETRIES3                   # Maximum retry attempts
```

## 🤖 Bot Commands

### Admin Commands
- `/start` - Start automatic wallpaper posting
- `/stop` - Stop the bot
- `/status` - Show current bot status
- `/stats` - Show detailed statistics
- `/send_batch` - Manually send a batch of wallpapers
- `/rotate_source` - Manually rotate to next source
- `/help` - Show help message

### 🎯 Wallpaper Categories
The bot now uses curated categories excluding people/girls:
- Nature, landscapes, mountains, forests
- Abstract, minimal, geometric designs
- Technology, cyberpunk, futuristic
- Anime, artistic, aesthetic
- Cities, architecture, urban scenes
- Animals, wildlife, macro photography
- Space, galaxy, cosmic themes
- And many more...

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f wallpaper-bot
```

### Manual Docker Build
```bash
# Build image
docker build -t wallpaper-bot .

# Run container
docker run -d \
  --name wallpaper-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  wallpaper-bot
```

## 🔍 Monitoring

### Bot Statistics
The bot tracks:
- Total wallpapers sent
- Success/failure rates
- Source usage statistics
- Daily sending patterns
- Error logs

### Health Checks
- Docker health checks included
- Log file monitoring
- Statistics file validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🆘 Support

For issues and questions:
1. Check the logs in `logs/wallpaper_bot.log`
2. Verify your configuration in `.env`
3. Check API key validity
4. Review bot permissions in Telegram

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram bot framework
- [Unsplash](https://unsplash.com/developers) for the wallpaper API
- [Pexels](https://www.pexels.com/api/) for the wallpaper API
- [Wallhaven](https://wallhaven.cc/help/api) for the wallpaper API

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.