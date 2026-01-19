"""
GitHub Followers Bot - Telegram Handler
Interactive Telegram bot with commands for managing the GitHub bot

Created by: dewhush
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

from core import GitHubFollowerBot

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Setup logging
logger = logging.getLogger(__name__)

# Global state
bot_instance: GitHubFollowerBot = None
is_farming = False
is_cleaning = False


def get_bot():
    """Get or initialize the bot instance"""
    global bot_instance
    if bot_instance is None:
        bot_instance = GitHubFollowerBot()
    return bot_instance


# Track last cleanup date
last_cleanup_date = None


async def execute_cleanup(bot, send_message_func):
    """Reusable cleanup logic"""
    try:
        # Get followers and following
        followers = {u.login for u in bot.user.get_followers()}
        following = {u.login for u in bot.user.get_following()}
        
        non_followers = following - followers
        
        if not non_followers:
            await send_message_func("✨ Sempurna! Semua following sudah followback.")
            return True
        else:
            await send_message_func(
                f"🔍 Ditemukan <b>{len(non_followers)}</b> akun yang tidak followback.\n"
                f"⏳ Memproses cleanup..."
            )
            
            unfollowed_count = 0
            
            for user in non_followers:
                try:
                    if bot.unfollow_user(user):
                        unfollowed_count += 1
                        
                        # Remove from tracked users
                        if user in bot.followed_users:
                            bot.followed_users.remove(user)
                        
                        # Progress update every 10 users
                        if unfollowed_count % 10 == 0:
                            await send_message_func(
                                f"📊 Progress: {unfollowed_count}/{len(non_followers)} di-unfollow..."
                            )
                        
                        await asyncio.sleep(2)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error unfollowing {user}: {e}")
                    continue
            
            # Save updated followers list
            bot._save_followed_users()
            
            # Send completion message
            completion_message = f"""
✅ <b>Cleanup Selesai!</b>

📊 <b>Hasil:</b>
├ Total non-followers: {len(non_followers)}
├ Berhasil unfollow: {unfollowed_count}
└ Gagal: {len(non_followers) - unfollowed_count}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            await send_message_func(completion_message)
            return True
            
    except Exception as e:
        logger.error(f"Error in execute_cleanup: {e}")
        await send_message_func(f"❌ Error saat cleanup: {str(e)}")
        return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = """
🚀 <b>GitHub Followers Bot</b>

Selamat datang! Bot ini membantu mengelola followers GitHub kamu.

<b>📝 Commands:</b>
/status - Lihat status bot
/clean - Bersihkan following & hentikan farming
/farm - Mulai farming followers
/stop - Hentikan semua proses
/help - Bantuan

✨ <i>Auto followback aktif di setiap farming cycle!</i>

<i>Created by: dewhush</i>
"""
    await update.message.reply_text(welcome_message, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = """
📖 <b>Panduan Penggunaan</b>

<b>/status</b>
Lihat status bot, jumlah following, followers, dan statistik.

<b>/clean</b>
Membersihkan following (unfollow non-followers) dan menghentikan farming. Setelah selesai, farming akan otomatis dilanjutkan.

<b>/farm</b>
Mulai farming followers dari target repositories.

<b>/stop</b>
Hentikan semua proses yang sedang berjalan.

<b>/help</b>
Menampilkan pesan bantuan ini.

✨ <i>Auto followback berjalan otomatis setiap farming cycle!</i>
"""
    await update.message.reply_text(help_message, parse_mode='HTML')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    try:
        bot = get_bot()
        
        followers = list(bot.user.get_followers())
        following = list(bot.user.get_following())
        
        status_message = f"""
📊 <b>Status Bot</b>

👤 <b>User:</b> {bot.user.login}
👥 <b>Followers:</b> {len(followers)}
👣 <b>Following:</b> {len(following)}
📦 <b>Tracked Users:</b> {len(bot.followed_users)}

🌾 <b>Farming:</b> {'🟢 Aktif' if is_farming else '🔴 Tidak aktif'}
🧹 <b>Cleaning:</b> {'🟢 Sedang berjalan' if is_cleaning else '🔴 Tidak aktif'}

⏰ <b>Waktu:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await update.message.reply_text(status_message, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /clean command
    - Stop farming
    - Clean following (unfollow non-followers)
    - Resume farming after cleanup
    """
    global is_farming, is_cleaning
    
    if is_cleaning:
        await update.message.reply_text("⏳ Proses cleaning sedang berjalan, mohon tunggu...")
        return
    
    try:
        is_cleaning = True
        was_farming = is_farming
        
        # Step 1: Stop farming
        if is_farming:
            is_farming = False
            await update.message.reply_text("🛑 Menghentikan farming sementara...")
            await asyncio.sleep(1)
        
        # Step 2: Start cleanup
        await update.message.reply_text("🧹 Memulai proses cleanup...")
        
        bot = get_bot()
        
        # Helper to send message with HTML parse mode
        async def send_msg(text):
            await update.message.reply_text(text, parse_mode='HTML')
            
        await execute_cleanup(bot, send_msg)
        
        is_cleaning = False
        
        # Step 3: Resume farming if it was active before
        if was_farming:
            await update.message.reply_text("🌾 Melanjutkan farming...")
            is_farming = True
            # Start farming in background
            asyncio.create_task(farming_background_task(context.bot, update.effective_chat.id))
        else:
            await update.message.reply_text(
                "✅ Cleanup selesai! Gunakan /farm untuk memulai farming.",
                parse_mode='HTML'
            )
            
    except Exception as e:
        is_cleaning = False
        logger.error(f"Error in clean_command: {e}")
        await update.message.reply_text(f"❌ Error saat cleanup: {str(e)}")


async def auto_followback(bot, telegram_bot=None, chat_id=None):
    """Automatically follow back new followers"""
    try:
        logger.info("🔄 Checking for new followers to followback...")
        
        current_followers = {u.login for u in bot.user.get_followers()}
        current_following = {u.login for u in bot.user.get_following()}
        
        not_following_back = current_followers - current_following
        
        if not_following_back:
            logger.info(f"🎉 Found {len(not_following_back)} followers to followback!")
            followed_count = 0
            new_follows = []
            
            for user in not_following_back:
                try:
                    if bot.follow_user(user):
                        followed_count += 1
                        new_follows.append(user)
                        bot.followed_users.add(user)
                        await asyncio.sleep(2)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error following back {user}: {e}")
                    continue
            
            bot._save_followed_users()
            logger.info(f"✅ Auto followback complete: {followed_count} users followed back")
            
            # Send Telegram notification
            if telegram_bot and chat_id and new_follows:
                users_list = "\n".join([f"👤 {u}" for u in new_follows])
                message = (
                    f"🎉 <b>New Followers Followed Back!</b>\n\n"
                    f"{users_list}\n\n"
                    f"✅ Total: {len(new_follows)}"
                )
                try:
                    await telegram_bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Failed to send telegram notification: {e}")
                    
        else:
            logger.info("✨ All followers already followed back")
            
    except Exception as e:
        logger.error(f"Auto followback error: {e}")


async def check_scheduled_cleanup(bot, telegram_bot, chat_id):
    """Check and run scheduled cleanup"""
    global last_cleanup_date, is_cleaning
    
    try:
        # Don't run if already cleaning
        if is_cleaning:
            return

        # Get schedule from config
        schedule = bot.config.get('cleanup_schedule', {})
        if not schedule.get('enabled', False):
            return

        target_time_str = schedule.get('specific_time', '02:30')
        target_time = datetime.strptime(target_time_str, '%H:%M').time()
        now = datetime.now()
        
        # Run if:
        # 1. Not run today yet
        # 2. Current time is past target time
        if last_cleanup_date != now.date() and now.time() >= target_time:
            logger.info("⏰ Starting scheduled cleanup...")
            
            if telegram_bot and chat_id:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text="⏰ <b>Scheduled Cleanup Started!</b>",
                    parse_mode='HTML'
                )
                
                async def send_msg(text):
                    await telegram_bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
                
                is_cleaning = True
                await execute_cleanup(bot, send_msg)
                is_cleaning = False
                last_cleanup_date = now.date()
                
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text="🌾 Returning to farming...",
                    parse_mode='HTML'
                )

    except Exception as e:
        logger.error(f"Error in scheduled cleanup: {e}")
        is_cleaning = False


async def farming_background_task_auto(telegram_bot, chat_id):
    """Background task for farming (auto-start version)"""
    global is_farming
    
    try:
        bot = get_bot()
        logger.info("🌾 Auto-farming started!")
        
        while is_farming:
            try:
                # Auto followback first
                await auto_followback(bot, telegram_bot, chat_id)
                
                # Check scheduled cleanup
                await check_scheduled_cleanup(bot, telegram_bot, chat_id)
                
                # Then farm
                if is_farming and not is_cleaning:
                    bot.farm_followers()
                
                await asyncio.sleep(300)  # 5 minutes between cycles
            except Exception as e:
                logger.error(f"Farming cycle error: {e}")
                await asyncio.sleep(60)
                
    except Exception as e:
        logger.error(f"Farming background task error: {e}")


async def farming_background_task(telegram_bot, chat_id):
    """Background task for farming (triggered by command)"""
    global is_farming
    
    try:
        bot = get_bot()
        
        while is_farming:
            try:
                # Auto followback first
                await auto_followback(bot, telegram_bot, chat_id)
                
                # Check scheduled cleanup
                await check_scheduled_cleanup(bot, telegram_bot, chat_id)
                
                # Then farm
                if is_farming and not is_cleaning:
                    bot.farm_followers()
                
                await asyncio.sleep(300)  # 5 minutes between cycles
            except Exception as e:
                logger.error(f"Farming cycle error: {e}")
                await asyncio.sleep(60)
                
    except Exception as e:
        logger.error(f"Farming background task error: {e}")


async def farm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /farm command - Start farming"""
    global is_farming
    
    if is_farming:
        await update.message.reply_text("🌾 Farming sudah berjalan!")
        return
    
    if is_cleaning:
        await update.message.reply_text("⏳ Tunggu proses cleaning selesai dulu...")
        return
    
    try:
        is_farming = True
        await update.message.reply_text(
            "🌾 <b>Farming dimulai!</b>\n\n"
            "Bot akan otomatis farming dari target repositories.\n"
            "Gunakan /stop untuk menghentikan.",
            parse_mode='HTML'
        )
        
        # Start farming in background
        asyncio.create_task(farming_background_task(context.bot, update.effective_chat.id))
        
    except Exception as e:
        is_farming = False
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def followback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /followback command - Follow back new followers"""
    try:
        await update.message.reply_text("🔍 Mencari followers baru...")
        
        bot = get_bot()
        
        # Get current followers and following
        current_followers = {u.login for u in bot.user.get_followers()}
        current_following = {u.login for u in bot.user.get_following()}
        
        # Find followers we haven't followed back
        not_following_back = current_followers - current_following
        
        if not not_following_back:
            await update.message.reply_text("✨ Kamu sudah follow balik semua followers!")
            return
        
        await update.message.reply_text(
            f"🎉 Ditemukan <b>{len(not_following_back)}</b> followers yang belum di-followback.\n"
            f"⏳ Memproses...",
            parse_mode='HTML'
        )
        
        followed_count = 0
        followed_users = []
        
        for user in not_following_back:
            try:
                if bot.follow_user(user):
                    followed_count += 1
                    followed_users.append(user)
                    
                    # Track in followed_users
                    bot.followed_users.add(user)
                    
                    # Progress update every 10 users
                    if followed_count % 10 == 0:
                        await update.message.reply_text(
                            f"📊 Progress: {followed_count}/{len(not_following_back)} di-follow..."
                        )
                    
                    await asyncio.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error following {user}: {e}")
                continue
        
        # Save updated followers list
        bot._save_followed_users()
        
        # Send completion message
        completion_message = f"""
✅ <b>Followback Selesai!</b>

📊 <b>Hasil:</b>
├ Total belum difollow: {len(not_following_back)}
├ Berhasil follow: {followed_count}
└ Gagal: {len(not_following_back) - followed_count}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await update.message.reply_text(completion_message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in followback_command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - Stop all processes"""
    global is_farming, is_cleaning
    
    stopped = []
    
    if is_farming:
        is_farming = False
        stopped.append("Farming")
    
    if is_cleaning:
        is_cleaning = False
        stopped.append("Cleaning")
    
    if stopped:
        await update.message.reply_text(
            f"🛑 Menghentikan: {', '.join(stopped)}\n\n"
            f"✅ Semua proses dihentikan."
        )
    else:
        await update.message.reply_text("ℹ️ Tidak ada proses yang sedang berjalan.")


async def set_commands(app: Application):
    """Set bot commands for the menu and auto-start farming"""
    global is_farming
    
    commands = [
        BotCommand("start", "Mulai bot"),
        BotCommand("status", "Lihat status bot"),
        BotCommand("clean", "Cleanup following & restart farming"),
        BotCommand("farm", "Mulai farming followers"),
        BotCommand("stop", "Hentikan semua proses"),
        BotCommand("help", "Bantuan"),
    ]
    await app.bot.set_my_commands(commands)
    
    # Auto-start farming when bot starts
    print("🌾 Auto-starting farming...")
    is_farming = True
    asyncio.create_task(farming_background_task_auto(app.bot, TELEGRAM_CHAT_ID))
    
    # Send notification to chat if TELEGRAM_CHAT_ID is set
    if TELEGRAM_CHAT_ID:
        try:
            await app.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="🚀 <b>Bot Started!</b>\n\n🌾 Farming otomatis dimulai.\nGunakan /status untuk cek status.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"Could not send startup notification: {e}")


def main():
    """Main function to run the Telegram bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    print("""
   _____ _ _   _       _       ____        _   
  / ____(_) | | |     | |     |  _ \\      | |  
 | |  __ _| |_| |__   | |_____| |_) | ___ | |_ 
 | | |_ | | __| '_ \\  | ______|  _ < / _ \\| __|
 | |__| | | |_| | | | | |     | |_) | (_) | |_ 
  \\_____|_|\\__|_| |_| |_|     |____/ \\___/ \\__|
                                               
            ✨ Telegram Bot Mode ✨
            Created by: dewhush
    """)
    
    # Create application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("clean", clean_command))
    app.add_handler(CommandHandler("farm", farm_command))
    app.add_handler(CommandHandler("stop", stop_command))
    
    # Set commands menu
    app.post_init = set_commands
    
    print(f"🚀 Bot started! Waiting for commands...")
    
    # Run the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
