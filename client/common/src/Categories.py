#!/usr/bin/env python

# Copyright (C) 2009,2010 Junta de Andalucia
# 
# Authors:
#   Roberto Majadas <roberto.majadas at openshine.com>
#   Cesar Garcia Tapia <cesar.garcia.tapia at openshine.com>
#   Luis de Bethencourt <luibg at openshine.com>
#   Pablo Vieytes <pvieytes at openshine.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import gettext
import __builtin__
__builtin__._ = gettext.gettext

category_strings = {
    # To translators : This string is a category name or a category description
    "abortion": (_("abortion"), _("Abortion information excluding when related to religion")),
    # To translators : This string is a category name or a category description
    "ads": (_("ads"), _("Advert servers and banned URLs")),
    # To translators : This string is a category name or a category description
    "adult": (_("adult"), _("Sites containing adult material such as swearing but not porn")),
    # To translators : This string is a category name or a category description
    "aggressive": (_("aggressive"), _("Similar to violence but more promoting than depicting")),
    # To translators : This string is a category name or a category description
    "antispyware": (_("antispyware"), _("Sites that remove spyware")),
    # To translators : This string is a category name or a category description
    "artnudes": (_("artnudes"), _("Art sites containing artistic nudity")),
    # To translators : This string is a category name or a category description
    "astrology": (_("astrology"), _("Astrology websites")),
    # To translators : This string is a category name or a category description
    "audio-video": (_("audio-video"), _("Sites with audio or video downloads")),
    # To translators : This string is a category name or a category description
    "banking": (_("banking"), _("Banking websites")),
    # To translators : This string is a category name or a category description
    "beerliquorinfo": (_("beerliquorinfo"), _("Sites with information only on beer or liquors")),
    # To translators : This string is a category name or a category description
    "beerliquorsale": (_("beerliquorsale"), _("Sites with beer or liquors for sale")),
    # To translators : This string is a category name or a category description
    "blog": (_("blog"), _("Journal/Diary websites")),
    # To translators : This string is a category name or a category description
    "cellphones": (_("cellphones"), _("stuff for mobile/cell phones")),
    # To translators : This string is a category name or a category description
    "chat": (_("chat"), _("Sites with chat rooms etc")),
    # To translators : This string is a category name or a category description
    "childcare": (_("childcare"), _("Sites to do with childcare")),
    # To translators : This string is a category name or a category description
    "cleaning": (_("cleaning"), _("Sites to do with cleaning")),
    # To translators : This string is a category name or a category description
    "clothing": (_("clothing"), _("Sites about and selling clothing")),
    # To translators : This string is a category name or a category description
    "contraception": (_("contraception"), _("Information about contraception")),
    # To translators : This string is a category name or a category description
    "culnary": (_("culnary"), _("Sites about cooking et al")),
    # To translators : This string is a category name or a category description
    "dating": (_("dating"), _("Sites about dating")),
    # To translators : This string is a category name or a category description
    "desktopsillies": (_("desktopsillies"), _("Sites containing screen savers, backgrounds, cursers, pointers. desktop themes and similar timewasting and potentially dangerous content")),
    # To translators : This string is a category name or a category description
    "dialers": (_("dialers"), _("Sites with dialers such as those for pornography or trojans")),
    # To translators : This string is a category name or a category description
    "drugs": (_("drugs"), _("Drug related sites")),
    # To translators : This string is a category name or a category description
    "ecommerce": (_("ecommerce"), _("Sites that provide online shopping")),
    # To translators : This string is a category name or a category description
    "entertainment": (_("entertainment"), _("Sites that promote movies, books, magazine, humor")),
    # To translators : This string is a category name or a category description
    "filehosting": (_("filehosting"), _("Sites to do with filehosting")),
    # To translators : This string is a category name or a category description
    "frencheducation": (_("frencheducation"), _("Sites to do with french education")),
    # To translators : This string is a category name or a category description
    "gambling": (_("gambling"), _("Gambling sites including stocks and shares")),
    # To translators : This string is a category name or a category description
    "games": (_("games"), _("Game related sites")),
    # To translators : This string is a category name or a category description
    "gardening": (_("gardening"), _("Gardening sites")),
    # To translators : This string is a category name or a category description
    "government": (_("government"), _("Military and schools etc")),
    # To translators : This string is a category name or a category description
    "guns": (_("guns"), _("Sites with guns")),
    # To translators : This string is a category name or a category description
    "hacking": (_("hacking"), _("Hacking/cracking information")),
    # To translators : This string is a category name or a category description
    "homerepair": (_("homerepair"), _("Sites about home repair")),
    # To translators : This string is a category name or a category description
    "hygiene": (_("hygiene"), _("Sites about hygiene and other personal grooming related stuff")),
    # To translators : This string is a category name or a category description
    "instantmessaging": (_("instantmessaging"), _("Sites that contain messenger client download and web-based messaging sites")),
    # To translators : This string is a category name or a category description
    "jewelry": (_("jewelry"), _("Sites about and selling jewelry")),
    # To translators : This string is a category name or a category description
    "jobsearch": (_("jobsearch"), _("Sites for finding jobs")),
    # To translators : This string is a category name or a category description
    "kidstimewasting": (_("kidstimewasting"), _("Sites kids often waste time on")),
    # To translators : This string is a category name or a category description
    "mail": (_("mail"), _("Webmail and email sites")),
    # To translators : This string is a category name or a category description
    "marketingware": (_("marketingware"), _("Sites about marketing products")),
    # To translators : This string is a category name or a category description
    "medical": (_("medical"), _("Medical websites")),
    # To translators : This string is a category name or a category description
    "mixed_adult": (_("mixed_adult"), _("Mixed adult content sites")),
    # To translators : This string is a category name or a category description
    "mobile-phone": (_("mobile-phone"), _("Sites to do with mobile phones")),
    # To translators : This string is a category name or a category description
    "naturism": (_("naturism"), _("Sites that contain nude pictures and/or promote a nude lifestyle")),
    # To translators : This string is a category name or a category description
    "news": (_("news"), _("News sites")),
    # To translators : This string is a category name or a category description
    "onlineauctions": (_("onlineauctions"), _("Online auctions")),
    # To translators : This string is a category name or a category description
    "onlinegames": (_("onlinegames"), _("Online gaming sites")),
    # To translators : This string is a category name or a category description
    "onlinepayment": (_("onlinepayment"), _("Online payment sites")),
    # To translators : This string is a category name or a category description
    "personalfinance": (_("personalfinance"), _("Personal finance sites")),
    # To translators : This string is a category name or a category description
    "pets": (_("pets"), _("Pet sites")),
    # To translators : This string is a category name or a category description
    "phishing": (_("phishing"), _("Sites attempting to trick people into giving out private information.")),
    # To translators : This string is a category name or a category description
    "porn": (_("porn"), _("Pornography")),
    # To translators : This string is a category name or a category description
    "proxy": (_("proxy"), _("Sites with proxies to bypass filters")),
    # To translators : This string is a category name or a category description
    "radio": (_("radio"), _("non-news related radio and television")),
    # To translators : This string is a category name or a category description
    "religion": (_("religion"), _("Sites promoting religion")),
    # To translators : This string is a category name or a category description
    "ringtones": (_("ringtones"), _("Sites containing ring tones, games, pictures and other")),
    # To translators : This string is a category name or a category description
    "searchengines": (_("searchengines"), _("Search engines such as google")),
    # To translators : This string is a category name or a category description
    "sect": (_("sect"), _("Sites about eligious groups")),
    # To translators : This string is a category name or a category description
    "sexuality": (_("sexuality"), _("Sites dedicated to sexuality, possibly including adult material")),
    # To translators : This string is a category name or a category description
    "shopping": (_("shopping"), _("Shopping sites")),
    # To translators : This string is a category name or a category description
    "socialnetworking": (_("socialnetworking"), _("Social networking websites")),
    # To translators : This string is a category name or a category description
    "sportnews": (_("sportnews"), _("Sport news sites")),
    # To translators : This string is a category name or a category description
    "sports": (_("sports"), _("All sport sites")),
    # To translators : This string is a category name or a category description
    "spyware": (_("spyware"), _("Sites who run or have spyware software to download")),
    # To translators : This string is a category name or a category description
    "updatesites": (_("updatesites"), _("Sites where software updates are downloaded from including virus sigs")),
    # To translators : This string is a category name or a category description
    "vacation": (_("vacation"), _("Sites about going on holiday")),
    # To translators : This string is a category name or a category description
    "violence": (_("violence"), _("Sites containing violence")),
    # To translators : This string is a category name or a category description
    "virusinfected": (_("virusinfected"), _("Sites who host virus infected files")),
    # To translators : This string is a category name or a category description
    "warez": (_("warez"), _("Sites with illegal pirate software")),
    # To translators : This string is a category name or a category description
    "weather": (_("weather"), _("Weather news sites and weather related")),
    # To translators : This string is a category name or a category description
    "weapons": (_("weapons"), _("Sites detailing or selling weapons")),
    # To translators : This string is a category name or a category description
    "webmail": (_("webmail"), _("Just webmail sites")),
    # To translators : This string is a category name or a category description
    "whitelist": (_("whitelist"), _("Contains site specifically 100% suitable for kids"))
}
