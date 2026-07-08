"""Système de tickets : panneau à bouton + salons privés.

- `ticket <salon> <message>` (admin) : poste `<message>` dans `<salon>` avec un
  bouton « Créer un ticket ». Le bouton est **persistant** (fonctionne après un
  redémarrage du bot).
- Un clic crée un salon privé `ticket-<n°>` visible uniquement par le membre et
  les administrateurs (qui outrepassent les permissions via Administrateur).
- `closeticket` (admin) : ferme le ticket courant et en retire le membre.

Les numéros de ticket sont un compteur monotone par serveur (voir
`storage.next_ticket_number`). Le propriétaire d'un ticket est mémorisé dans le
topic du salon (`owner: <id>`), à la manière du confinement.
"""
import logging

import discord
from discord.ext import commands

from utils import checks, storage
from utils.i18n import t

log = logging.getLogger("action")

CATEGORY_NAME = "tickets"
BUTTON_ID = "ticket:create"  # custom_id stable → bouton persistant.
_OWNER_MARKER = "owner:"


def _owner_id_from_topic(topic: str | None) -> int | None:
    """Extrait l'ID du propriétaire depuis le topic (marqueur `owner: <id>`)."""
    if not topic or _OWNER_MARKER not in topic:
        return None
    after = topic.split(_OWNER_MARKER, 1)[1]
    digits = "".join(c for c in after if c.isdigit() or c == " ").split()
    return int(digits[0]) if digits else None


def _find_open_ticket(
    guild: discord.Guild, member_id: int
) -> discord.TextChannel | None:
    """Salon de ticket ouvert appartenant à un membre, ou None."""
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        return None
    marker = f"{_OWNER_MARKER} {member_id}"
    for channel in category.text_channels:
        if channel.name.startswith("ticket-") and channel.topic \
                and marker in channel.topic:
            return channel
    return None


async def _create_ticket(
    guild: discord.Guild, member: discord.Member
) -> discord.TextChannel:
    """Crée le salon de ticket privé du membre et renvoie le salon."""
    # Catégorie « tickets », masquée à @everyone (les admins la voient via
    # leur permission Administrateur).
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(
            CATEGORY_NAME,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                guild.me: discord.PermissionOverwrite(view_channel=True),
            },
            reason="Système de tickets",
        )

    number = storage.next_ticket_number(guild.id)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
        member: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
    }
    channel = await guild.create_text_channel(
        name=f"ticket-{number}",
        category=category,
        overwrites=overwrites,
        topic=f"Ticket #{number} — {member} ({_OWNER_MARKER} {member.id})",
        reason=f"Ticket ouvert par {member}",
    )
    return channel


class TicketView(discord.ui.View):
    """Vue persistante : bouton « Créer un ticket »."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Créer un ticket / Open a ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id=BUTTON_ID,
    )
    async def create(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            return
        # Un seul ticket ouvert à la fois par membre.
        existing = _find_open_ticket(guild, member.id)
        if existing is not None:
            await interaction.response.send_message(
                t(guild, "ticket.already_open", channel=existing.mention),
                ephemeral=True,
            )
            return
        if not guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(
                t(guild, "ticket.bot_no_perm"), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        try:
            channel = await _create_ticket(guild, member)
        except discord.HTTPException:
            await interaction.followup.send(
                t(guild, "ticket.create_failed"), ephemeral=True
            )
            return
        prefix = storage.get_prefix(guild.id)
        await channel.send(
            t(guild, "ticket.welcome", user=member.mention, prefix=prefix)
        )
        log.info("Ticket %s ouvert par %s sur %s", channel.name, member,
                 guild.name)
        await interaction.followup.send(
            t(guild, "ticket.created", channel=channel.mention), ephemeral=True
        )


class Ticket(commands.Cog):
    """Système de tickets (réservé aux administrateurs)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        # Enregistre la vue persistante : le bouton reste actif après un
        # redémarrage, même sur d'anciens panneaux.
        self.bot.add_view(TicketView())

    @commands.hybrid_command(
        name="ticket",
        description="Crée un panneau de ticket (bouton) dans un salon.",
    )
    @checks.admin()
    @commands.bot_has_permissions(manage_channels=True)
    async def ticket(
        self, ctx: commands.Context, salon: discord.TextChannel, *, message: str
    ) -> None:
        embed = discord.Embed(
            description=message,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=t(ctx, "ticket.panel_footer"))
        try:
            await salon.send(embed=embed, view=TicketView())
        except discord.Forbidden:
            await ctx.send(t(ctx, "ticket.panel_forbidden", channel=salon.mention))
            return
        await ctx.send(t(ctx, "ticket.panel_posted", channel=salon.mention))

    @commands.hybrid_command(
        name="closeticket",
        description="Ferme le ticket courant et en retire le membre.",
    )
    @checks.admin()
    async def closeticket(self, ctx: commands.Context) -> None:
        channel = ctx.channel
        category = getattr(channel, "category", None)
        if category is None or category.name != CATEGORY_NAME \
                or not channel.name.startswith("ticket-"):
            await ctx.send(t(ctx, "ticket.not_a_ticket"))
            return

        owner_id = _owner_id_from_topic(channel.topic)
        # Retire l'accès du membre qui a ouvert le ticket.
        if owner_id is not None:
            member = ctx.guild.get_member(owner_id)
            if member is not None:
                try:
                    await channel.set_permissions(
                        member, overwrite=None, reason="Ticket fermé"
                    )
                except discord.HTTPException:
                    pass

        await ctx.send(t(ctx, "ticket.closed", user=ctx.author.mention))
        # Renomme le salon pour marquer la fermeture (conservé pour les admins).
        try:
            await channel.edit(
                name=channel.name.replace("ticket-", "closed-", 1),
                reason=f"Ticket fermé par {ctx.author}",
            )
        except discord.HTTPException:
            pass
        log.info("Ticket %s fermé par %s", channel.name, ctx.author)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ticket(bot))
