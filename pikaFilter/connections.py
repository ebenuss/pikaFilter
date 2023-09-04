import logging, pyrogram 
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from FilterBot.database import db
from configs import ADMINS

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message((filters.private | filters.group) & filters.command('connect'))
async def addconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"Sen anonim bir yöneticisin. PM'de /connect {message.chat.id} kullanın")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        try:
            cmd, group_id = message.text.split(" ", 1)
        except:
            await message.reply_text(
                "<b>Doğru biçimde girin!</b>\n\n"
                "<code>/connect grup kimliği</code>\n\n"
                "<i>Bu botu grubunuza ekleyerek Grup kimliğinizi alın ve <code>/id</code></i> kullanın",
                quote=True
            )
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

    try:
        st = await client.get_chat_member(group_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and userid not in ADMINS
        ):
            await message.reply_text("Given grubunda yönetici olmalısınız!", quote=True)
            return
    except Exception as e:
        logger.exception(e)
        await message.reply_text(
            "Geçersiz Grup Kimliği!\n\nDoğruysa grubunuzda bulunduğumdan emin olun!!",
            quote=True,
        )

        return
    try:
        st = await client.get_chat_member(group_id, "me")
        if st.status == enums.ChatMemberStatus.ADMINISTRATOR:
            ttl = await client.get_chat(group_id)
            title = ttl.title

            addcon = await db.add_connection(str(group_id), str(userid))
            if addcon:
                await message.reply_text(
                    f"**{title}** ile başarıyla bağlantı kuruldu\nArtık grubunuzu özel mesajımdan yönetin!",
                    quote=True,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
                if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    await client.send_message(
                        userid,
                        f"**{title}** ile bağlantı kuruldu !",
                        parse_mode=enums.ParseMode.MARKDOWN
                    )
            else:
                await message.reply_text(
                    "Bu sohbete zaten bağlısınız!",
                    quote=True
                )
        else:
            await message.reply_text("Beni gruba yönetici olarak ekle", quote=True)
    except Exception as e:
        logger.exception(e)
        await message.reply_text('Bir hata oluştu! Daha sonra tekrar deneyin.', quote=True)
        return


@Client.on_message((filters.private | filters.group) & filters.command('disconnect'))
async def deleteconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"Sen anonim bir yöneticisin. PM'de /connect {message.chat.id} kullanın")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text("Grupları görüntülemek veya bağlantıyı kesmek için /connections komutunu çalıştırın!", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

        st = await client.get_chat_member(group_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            return

        delcon = await db.delete_connection(str(userid), str(group_id))
        if delcon:
            await message.reply_text("Bu sohbetle bağlantı başarıyla kesildi", quote=True)
        else:
            await message.reply_text("Bu sohbet bana bağlı değil!\nBağlanmak için /connect yapın.", quote=True)

@Client.on_message(filters.private & filters.command(["connections"]))
async def connections(client, message):
    userid = message.from_user.id

    groupids = await db.all_connections(str(userid))
    if groupids is None:
        await message.reply_text(
            "Aktif bağlantı yok!! Önce bazı gruplara bağlanın.",
            quote=True
        )
        return
    buttons = []
    for groupid in groupids:
        try:
            ttl = await client.get_chat(int(groupid))
            title = ttl.title
            active = await db.if_active(str(userid), str(groupid))
            act = " - ACTIVE" if active else ""
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                    )
                ]
            )
        except:
            pass
    if buttons:
        await message.reply_text(
            "Bağlı grup ayrıntılarınız ;\n\n",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    else:
        await message.reply_text(
            "Aktif bağlantı yok!! Önce bazı gruplara bağlanın.",
            quote=True
        )
