"""Commandes `note` / `delnote` : notes libres au dossier d'un utilisateur.

Les notes sont affichées par `userstatus` (dossier). Utile pour consigner un
contexte qui n'est pas une sanction (ex. « déjà prévenu en MP », « ami de X »).
"""
import discord
from discord.ext import commands

from utils import checks, embeds, storage
from utils.i18n import t

# Longueur maximale d'une note (pour rester lisible dans l'embed userstatus).
MAX_NOTE_LEN = 500


class Note(commands.Cog):
    """Notes de dossier d'un utilisateur (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="note",
        description="Ajoute une note au dossier d'un utilisateur (userstatus).",
    )
    @checks.admin()
    async def note(
        self, ctx: commands.Context, member: discord.Member, *, texte: str
    ) -> None:
        texte = texte.strip()
        if not texte:
            await ctx.send(embed=embeds.error(t(ctx, "note.empty")))
            return
        if len(texte) > MAX_NOTE_LEN:
            await ctx.send(embed=embeds.error(
                t(ctx, "note.too_long", max=MAX_NOTE_LEN)))
            return
        storage.add_note(ctx.guild.id, member.id, ctx.author.id, texte)
        count = len(storage.get_notes(ctx.guild.id, member.id))
        await ctx.send(embed=embeds.success(
            t(ctx, "note.added", user=member.mention, index=count)))

    @commands.hybrid_command(
        name="delnote",
        description="Supprime une note du dossier d'un utilisateur (par numéro).",
    )
    @checks.admin()
    async def delnote(
        self, ctx: commands.Context, member: discord.Member, numero: int
    ) -> None:
        # Les notes sont numérotées à partir de 1 côté utilisateur.
        removed = storage.remove_note(ctx.guild.id, member.id, numero - 1)
        if removed is None:
            await ctx.send(embed=embeds.error(
                t(ctx, "note.bad_index", user=member.mention)))
            return
        await ctx.send(embed=embeds.success(
            t(ctx, "note.removed", user=member.mention, index=numero)))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Note(bot))
