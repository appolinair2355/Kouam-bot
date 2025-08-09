# Telegram Deployment Bot

## Overview
This project is a Python-based Telegram bot that facilitates the distribution of deployment zip files to users. Built with Flask, it integrates with Telegram's Bot API via webhooks, making it suitable for cloud deployment. The bot's core purpose is to provide an efficient and automated way to deliver application deployment packages, aiming to streamline development and deployment workflows for users by offering immediate access to necessary files.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes
- 2025-08-09: Updated prediction channel ID to -1002875505624 per user request
- 2025-08-09: Fixed status update system to properly recognize completion indicators 🔰 and ✅
- 2025-08-09: Enhanced has_completion_indicators() and is_final_message() methods with detailed logging
- 2025-08-09: URL corrected to https://kouam-bot-1foc.onrender.com for Render.com deployment
- 2025-08-09: Fixed deployment file path in handlers.py for /deploy command
- 2025-08-09: Added /ni command to send modified files package directly
- 2025-08-09: Fixed /ni command and created deployer33.zip with all updated files
- 2025-08-09: Package deployer33.zip contains all corrections and latest modifications
- 2025-08-09: Optimized verification system - immediate status updates when costume found
- 2025-08-09: Reduced failure detection from 4 games to 2 games for faster response
- 2025-08-09: Created deployer34.zip with accelerated verification system
- 2025-08-09: Optimized sequential verification - immediate stop when costume found
- 2025-08-09: Sequential checks: 0→✅0️⃣, +1→✅1️⃣, +2→✅2️⃣, +3→✅3️⃣, fail→📍⭕
- 2025-08-09: Created deployer35.zip with sequential verification system
- 2025-08-09: Removed Benin flags from all messages and status displays for cleaner look
- 2025-08-09: Created deployer36.zip with clean display without flags

## System Architecture

The application employs a simple three-tier architecture:
1.  **Web Layer**: Flask application handling HTTP requests and webhooks.
2.  **Bot Logic Layer**: Telegram bot implementation for message processing.
3.  **Configuration Layer**: Environment-based configuration management.

The bot utilizes a webhook-based approach, optimized for cloud deployment platforms requiring HTTP endpoints.

### Core Architectural Decisions & Design Patterns

*   **Webhook-based Communication**: Prioritizes real-time updates and efficient resource usage over polling.
*   **Modular Design**: Separation of concerns into `main.py` (Flask web server), `bot.py` (Telegram bot logic), and `config.py` (configuration management) for maintainability.
*   **Stateless Design**: Ensures scalability and easy deployment in containerized environments.
*   **Environment-based Configuration**: Utilizes environment variables for sensitive information and flexible deployment.

### Key Components

*   **Flask Web Server (`main.py`)**: Manages HTTP requests, including Telegram webhooks (`/webhook`), health checks (`/health`), and a root endpoint (`/`).
*   **Telegram Bot Handler (`bot.py`)**: Contains the core bot logic, processing Telegram messages, handling commands like `/start`, and managing the distribution of `deployment.zip` files. It also includes sophisticated message processing for prediction and verification, handling temporary and final messages, and managing prediction rules based on specific card combinations and positions.
*   **Configuration Management (`config.py`)**: Centralizes configuration, parses environment variables, performs validation, and handles webhook URL construction.

### Feature Specifications

*   **File Distribution**: Sends `deployment.zip` to users upon request.
*   **Advanced Prediction System**:
    *   Triggers on edited channel messages with "✅".
    *   Analyzes the second parenthesis for exactly 3 cards.
    *   Prediction rules based on card patterns (e.g., first card different from others, or all three identical).
    *   Formats predictions clearly: "🔵🇧🇯[N+2] costume :[COSTUME] statut :⏳🇧🇯".
*   **Sequential Verification System**:
    *   Triggers on edited messages with "✅".
    *   Verifies predicted suits against message content with sequential offsets (0, +1, +2, +3).
    *   Updates prediction messages with verification statuses (e.g., ✅0️⃣🇧🇯, ✅1️⃣🇧🇯, 📍⭕📍🇧🇯).
*   **Authorization System**: Restricts bot access to an authorized user ID, protecting all commands and logging unauthorized attempts.
*   **Configurable Cooldown**: Allows dynamic adjustment of prediction cooldown via `/cooldown [seconds]`, with persistence across bot restarts.
*   **Multi-channel Redirection**: Enables advanced configuration of message redirection from source to target channels via `/redirect`, supporting multiple persistent redirects.
*   **Enhanced User Interface**: Provides detailed, interactive help messages, clear examples, and professional formatting for all commands.
*   **Announcement Command**: Allows authorized users to broadcast official announcements to configured prediction channels via `/announce [message]`.
*   **Card Prediction Rules**: Implements specific rules for predicting suits based on identical card combinations (e.g., three diamonds predict clubs).

## External Dependencies

*   **Telegram Bot API**: Used for all bot interactions, including receiving messages via webhooks and sending text messages and files. Authenticated via a bot token.
*   **Deployment Platform (render.com)**: The primary deployment target, requiring `PORT` environment variable support, HTTPS endpoints for webhooks, and health check monitoring.
*   **Python Libraries**:
    *   `Flask`: Web framework for handling HTTP requests.
    *   `requests`: HTTP client for making calls to the Telegram API.
    *   `os`, `logging`, `json`: Standard library modules for core functionality, environment variable access, logging, and JSON processing.