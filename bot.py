import os
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
JUPITER_API = "https://price.jup.ag/v4/price"
JUPITER_SWAP = "https://quote-api.jup.ag/v6"

# Top Solana tokens
TOKENS = {
    "SOL":   {"mint": "So11111111111111111111111111111111111111112",  "name": "Solana"},
    "JUP":   {"mint": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", "name": "Jupiter"},
    "BONK":  {"mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263","name": "Bonk"},
    "WIF":   {"mint": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", "name": "dogwifhat"},
    "PYTH":  {"mint": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3", "name": "Pyth Network"},
    "RAY":   {"mint": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",  "name": "Raydium"},
    "ORCA":  {"mint": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",  "name": "Orca"},
    "MNGO":  {"mint": "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac",  "name": "Mango"},
    "SAMO":  {"mint": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU", "name": "Samoyedcoin"},
    "MSOL":  {"mint": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",  "name": "Marinade SOL"},
}

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

user_wallets = {}
user_alerts = {}

async def fetch_prices(symbols: list) -> dict:
    ids = ",".join([TOKENS[s]["mint"] for s in symbols if s in TOKENS])
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{JUPITER_API}?ids={ids}") as resp:
            data = await resp.json()
            return data.get("data", {})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Ver Preços", callback_data="prices"),
         InlineKeyboardButton("🔔 Alertas", callback_data="alerts_menu")],
        [InlineKeyboardButton("💱 Swap / Operar", callback_data="swap_menu"),
         InlineKeyboardButton("💼 Carteira", callback_data="wallet_menu")],
        [InlineKeyboardButton("📈 Top Gainers", callback_data="gainers")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👑 *Solana Crypto Bot*\n\n"
        "Monitore e opere as principais criptos da rede Solana!\n\n"
        "Escolha uma opção abaixo:",
        parse_mode="Markdown",
        reply_markup=markup
    )

async def prices_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Buscando preços...")

    symbols = list(TOKENS.keys())
    prices = await fetch_prices(symbols)

    msg = "📊 *Preços ao Vivo — Solana Network*\n\n"
    for symbol, info in TOKENS.items():
        mint = info["mint"]
        p = prices.get(mint, {})
        price = p.get("price", 0)
        if price:
            msg += f"*{symbol}* ({info['name']})\n"
            msg += f"  💵 ${price:,.6f}\n\n"

    keyboard = [[InlineKeyboardButton("🔄 Atualizar", callback_data="prices"),
                 InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def gainers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Buscando dados...")

    symbols = list(TOKENS.keys())
    prices = await fetch_prices(symbols)

    token_data = []
    for symbol, info in TOKENS.items():
        mint = info["mint"]
        p = prices.get(mint, {})
        price = p.get("price", 0)
        change = p.get("extraInfo", {}).get("lastSwappedPrice", {})
        token_data.append((symbol, info["name"], price))

    token_data.sort(key=lambda x: x[2], reverse=True)

    msg = "📈 *Top Tokens — Solana Network*\n_(por valor de mercado)_\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, (symbol, name, price) in enumerate(token_data[:10]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        msg += f"{medal} *{symbol}* — ${price:,.4f}\n"

    keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def swap_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = (
        "💱 *Swap / Operar*\n\n"
        "Para realizar swaps reais na Solana, você precisa:\n\n"
        "1️⃣ Ter uma carteira Solana (Phantom, Solflare)\n"
        "2️⃣ Exportar sua *chave privada* (com cuidado!)\n"
        "3️⃣ Configurar a variável `WALLET_PRIVATE_KEY`\n\n"
        "⚠️ *NUNCA compartilhe sua chave privada com ninguém!*\n\n"
        "Use os botões abaixo para simular um swap:"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Simular SOL → USDC", callback_data="sim_sol_usdc"),
         InlineKeyboardButton("🔄 Simular BONK → SOL", callback_data="sim_bonk_sol")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
    ]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def simulate_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "sim_sol_usdc":
        inp = TOKENS["SOL"]["mint"]
        out = USDC_MINT
        amount = 1_000_000_000  # 1 SOL
        label = "1 SOL → USDC"
    else:
        inp = TOKENS["BONK"]["mint"]
        out = TOKENS["SOL"]["mint"]
        amount = 1_000_000  # 1M BONK
        label = "1.000.000 BONK → SOL"

    await query.edit_message_text(f"⏳ Buscando cotação: {label}...")

    url = f"{JUPITER_SWAP}/quote?inputMint={inp}&outputMint={out}&amount={amount}&slippageBps=50"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        out_amount = int(data.get("outAmount", 0))
        price_impact = data.get("priceImpactPct", 0)

        if query.data == "sim_sol_usdc":
            out_fmt = f"${out_amount / 1_000_000:.2f} USDC"
        else:
            out_fmt = f"{out_amount / 1_000_000_000:.4f} SOL"

        msg = (
            f"📊 *Simulação de Swap*\n\n"
            f"🔄 {label}\n"
            f"✅ Você receberia: *{out_fmt}*\n"
            f"📉 Price Impact: {float(price_impact):.4f}%\n\n"
            f"_Dados via Jupiter Aggregator_"
        )
    except Exception as e:
        msg = f"❌ Erro ao buscar cotação: {str(e)}"

    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="swap_menu"),
                 InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def alerts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    alerts = user_alerts.get(uid, [])

    msg = "🔔 *Alertas de Preço*\n\n"
    if alerts:
        for a in alerts:
            msg += f"• {a['symbol']} {'acima' if a['above'] else 'abaixo'} de ${a['price']}\n"
    else:
        msg += "Nenhum alerta configurado.\n"

    msg += "\nPara criar um alerta, envie:\n`/alerta SOL 150` _(avisa quando SOL > $150)_\n`/alerta SOL -120` _(avisa quando SOL < $120)_"

    keyboard = [
        [InlineKeyboardButton("🗑 Limpar Alertas", callback_data="clear_alerts")],
        [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
    ]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("❌ Uso: `/alerta SOL 150` ou `/alerta SOL -120`", parse_mode="Markdown")
        return

    symbol = args[0].upper()
    if symbol not in TOKENS:
        await update.message.reply_text(f"❌ Token desconhecido. Use: {', '.join(TOKENS.keys())}")
        return

    try:
        price = float(args[1])
    except ValueError:
        await update.message.reply_text("❌ Preço inválido.")
        return

    above = price > 0
    price = abs(price)

    if uid not in user_alerts:
        user_alerts[uid] = []

    user_alerts[uid].append({"symbol": symbol, "price": price, "above": above, "chat_id": update.message.chat_id})
    direction = "acima" if above else "abaixo"
    await update.message.reply_text(f"✅ Alerta criado! Você será notificado quando *{symbol}* estiver {direction} de *${price}*", parse_mode="Markdown")

async def clear_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    user_alerts[uid] = []
    await query.edit_message_text("✅ Alertas removidos!", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]
    ))

async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = (
        "💼 *Carteira Solana*\n\n"
        "Para verificar saldo de uma carteira, envie:\n"
        "`/carteira SEU_ENDERECO_SOLANA`\n\n"
        "Exemplo:\n`/carteira 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM`"
    )
    keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]
    await query.edit_message_text(msg, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def check_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Uso: `/carteira ENDERECO`", parse_mode="Markdown")
        return

    address = context.args[0]
    await update.message.reply_text(f"⏳ Verificando carteira `{address[:8]}...`", parse_mode="Markdown")

    url = "https://api.mainnet-beta.solana.com"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()

        lamports = data.get("result", {}).get("value", 0)
        sol = lamports / 1_000_000_000

        prices = await fetch_prices(["SOL"])
        sol_price = prices.get(TOKENS["SOL"]["mint"], {}).get("price", 0)
        usd_value = sol * sol_price

        msg = (
            f"💼 *Saldo da Carteira*\n\n"
            f"📍 `{address[:8]}...{address[-4:]}`\n\n"
            f"◎ SOL: *{sol:.4f}*\n"
            f"💵 Valor: *${usd_value:,.2f} USD*"
        )
    except Exception as e:
        msg = f"❌ Erro: {str(e)}"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📊 Ver Preços", callback_data="prices"),
         InlineKeyboardButton("🔔 Alertas", callback_data="alerts_menu")],
        [InlineKeyboardButton("💱 Swap / Operar", callback_data="swap_menu"),
         InlineKeyboardButton("💼 Carteira", callback_data="wallet_menu")],
        [InlineKeyboardButton("📈 Top Gainers", callback_data="gainers")],
    ]
    await query.edit_message_text(
        "👑 *Solana Crypto Bot*\n\nEscolha uma opção:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    if not user_alerts:
        return

    all_symbols = list(TOKENS.keys())
    prices = await fetch_prices(all_symbols)

    for uid, alerts in list(user_alerts.items()):
        for alert in alerts[:]:
            mint = TOKENS[alert["symbol"]]["mint"]
            current = prices.get(mint, {}).get("price", 0)
            if not current:
                continue
            triggered = (alert["above"] and current >= alert["price"]) or \
                        (not alert["above"] and current <= alert["price"])
            if triggered:
                direction = "subiu acima" if alert["above"] else "caiu abaixo"
                await context.bot.send_message(
                    chat_id=alert["chat_id"],
                    text=f"🚨 *ALERTA!* {alert['symbol']} {direction} de ${alert['price']}!\nPreço atual: ${current:,.4f}",
                    parse_mode="Markdown"
                )
                alerts.remove(alert)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alerta", set_alert))
    app.add_handler(CommandHandler("carteira", check_wallet))

    app.add_handler(CallbackQueryHandler(prices_handler, pattern="^prices$"))
    app.add_handler(CallbackQueryHandler(gainers_handler, pattern="^gainers$"))
    app.add_handler(CallbackQueryHandler(swap_menu_handler, pattern="^swap_menu$"))
    app.add_handler(CallbackQueryHandler(simulate_swap, pattern="^sim_"))
    app.add_handler(CallbackQueryHandler(alerts_menu, pattern="^alerts_menu$"))
    app.add_handler(CallbackQueryHandler(clear_alerts, pattern="^clear_alerts$"))
    app.add_handler(CallbackQueryHandler(wallet_menu, pattern="^wallet_menu$"))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))

    app.job_queue.run_repeating(check_alerts_job, interval=60, first=10)

    print("🚀 Bot Solana rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
