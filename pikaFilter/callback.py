import ast, pyrogram 
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pikaFilter.database import db
from configs import ADMINS

@Client.on_callback_query(filters.regex("(close_data|delallconfirm|delallcancel|groupcb|connectcb|disconnect|deletecb|backcb|alertmessage)"))
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await db.active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Grubunuzda bulunduğumdan emin olun!!", quote=True)
                    return await query.answer('Korsanlık Suçtur')
            else:
                await query.message.edit_text(
                    "Hiçbir gruba bağlı değilim!\n/connections'ı kontrol edin veya herhangi bir gruba bağlanın",
                    quote=True
                )
                return await query.answer('Korsanlık Suçtur')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Korsanlık Suçtur')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await db.del_all(query.message, grp_id, title)
        else:
            await query.answer("Bunu yapmak için Grup Sahibi veya Yetki Kullanıcısı olmanız gerekir!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Bu sana göre değil!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Grup Adı : **{title}**\nGrup Kimliği : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Korsanlık Suçtur')
    elif "connectcb" in query.data: 
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await db.make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"**{title}** ile bağlantı kuruldu",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Bir hata oluştu!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('Korsanlık Suçtur')
    elif "disconnect" in query.data: 
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await db.make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"**{title}** ile bağlantı kesildi",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Bir hata oluştu!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Korsanlık Suçtur')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await db.delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Bağlantı başarıyla silindi"
            )
        else:
            await query.message.edit_text(
                f"Bir hata oluştu!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Korsanlık Suçtur')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await db.all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "Aktif bağlantı yok!! Önce bazı gruplara bağlanın.",
            )
            return await query.answer('Korsanlık Suçtur')
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
            await query.message.edit_text(
                "Bağlı grup ayrıntılarınız ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await db.find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
