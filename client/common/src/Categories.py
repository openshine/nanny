#!/usr/bin/env python

# Copyright (C) 2009 Junta de Andalucia
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
	"abortion": (_("abortion"), _("Abortion information excluding when related to religion")),
	"ads": (_("ads"), _("Advert servers and banned URLs")),
	"adult": (_("adult"), _("Sites containing adult material such as swearing but not porn")),
	"aggressive": (_("aggressive"), _("Similar to violence but more promoting than depicting")),
	"antispyware": (_("antispyware"), _("Sites that remove spyware")),
	"artnudes": (_("artnudes"), _("Art sites containing artistic nudity")),
	"astrology": (_("astrology"), _("Astrology websites")),
	"audio-video": (_("audio-video"), _("Sites with audio or video downloads")),
	"banking": (_("banking"), _("Banking websites")),
	"beerliquorinfo": (_("beerliquorinfo"), _("Sites with information only on beer or liquors")),
	"beerliquorsale": (_("beerliquorsale"), _("Sites with beer or liquors for sale")),
	"blog": (_("blog"), _("Journal/Diary websites")),
	"cellphones": (_("cellphones"), _("stuff for mobile/cell phones")),
	"chat": (_("chat"), _("Sites with chat rooms etc")),
	"childcare": (_("childcare"), _("Sites to do with childcare")),
	"cleaning": (_("cleaning"), _("Sites to do with cleaning")),
	"clothing": (_("clothing"), _("Sites about and selling clothing")),
	"contraception": (_("contraception"), _("Information about contraception")),
	"culnary": (_("culnary"), _("Sites about cooking et al")),
	"dating": (_("dating"), _("Sites about dating")),
	"desktopsillies": (_("desktopsillies"), _("Sites containing screen savers, backgrounds, cursers, pointers. desktop themes and similar timewasting and potentially dangerous content")),
	"dialers": (_("dialers"), _("Sites with dialers such as those for pornography or trojans")),
	"drugs": (_("drugs"), _("Drug related sites")),
	"ecommerce": (_("ecommerce"), _("Sites that provide online shopping")),
	"entertainment": (_("entertainment"), _("Sites that promote movies, books, magazine, humor")),
	"filehosting": (_("filehosting"), _("Sites to do with filehosting")),
	"frencheducation": (_("frencheducation"), _("Sites to do with french education")),
	"gambling": (_("gambling"), _("Gambling sites including stocks and shares")),
	"games": (_("games"), _("Game related sites")),
	"gardening": (_("gardening"), _("Gardening sites")),
	"government": (_("government"), _("Military and schools etc")),
	"guns": (_("guns"), _("Sites with guns")),
	"hacking": (_("hacking"), _("Hacking/cracking information")),
	"homerepair": (_("homerepair"), _("Sites about home repair")),
	"hygiene": (_("hygiene"), _("Sites about hygiene and other personal grooming related stuff")),
	"instantmessaging": (_("instantmessaging"), _("Sites that contain messenger client download and web-based messaging sites")),
	"jewelry": (_("jewelry"), _("Sites about and selling jewelry")),
	"jobsearch": (_("jobsearch"), _("Sites for finding jobs")),
	"kidstimewasting": (_("kidstimewasting"), _("Sites kids often waste time on")),
	"mail": (_("mail"), _("Webmail and email sites")),
	"marketingware": (_("marketingware"), _("Sites about marketing products")),
	"medical": (_("medical"), _("Medical websites")),
	"mixed_adult": (_("mixed_adult"), _("Mixed adult content sites")),
	"mobile-phone": (_("mobile-phone"), _("Sites to do with mobile phones")),
	"naturism": (_("naturism"), _("Sites that contain nude pictures and/or promote a nude lifestyle")),
	"news": (_("news"), _("News sites")),
	"onlineauctions": (_("onlineauctions"), _("Online auctions")),
	"onlinegames": (_("onlinegames"), _("Online gaming sites")),
	"onlinepayment": (_("onlinepayment"), _("Online payment sites")),
	"personalfinance": (_("personalfinance"), _("Personal finance sites")),
	"pets": (_("pets"), _("Pet sites")),
	"phishing": (_("phishing"), _("Sites attempting to trick people into giving out private information.")),
	"porn": (_("porn"), _("Pornography")),
	"proxy": (_("proxy"), _("Sites with proxies to bypass filters")),
	"radio": (_("radio"), _("non-news related radio and television")),
	"religion": (_("religion"), _("Sites promoting religion")),
	"ringtones": (_("ringtones"), _("Sites containing ring tones, games, pictures and other")),
	"searchengines": (_("searchengines"), _("Search engines such as google")),
	"sect": (_("sect"), _("Sites about eligious groups")),
	"sexuality": (_("sexuality"), _("Sites dedicated to sexuality, possibly including adult material")),
	"shopping": (_("shopping"), _("Shopping sites")),
	"socialnetworking": (_("socialnetworking"), _("Social networking websites")),
	"sportnews": (_("sportnews"), _("Sport news sites")),
	"sports": (_("sports"), _("All sport sites")),
	"spyware": (_("spyware"), _("Sites who run or have spyware software to download")),
	"updatesites": (_("updatesites"), _("Sites where software updates are downloaded from including virus sigs")),
	"vacation": (_("vacation"), _("Sites about going on holiday")),
	"violence": (_("violence"), _("Sites containing violence")),
	"virusinfected": (_("virusinfected"), _("Sites who host virus infected files")),
	"warez": (_("warez"), _("Sites with illegal pirate software")),
	"weather": (_("weather"), _("Weather news sites and weather related")),
	"weapons": (_("weapons"), _("Sites detailing or selling weapons")),
	"webmail": (_("webmail"), _("Just webmail sites")),
	"whitelist": (_("whitelist"), _("Contains site specifically 100% suitable for kids"))
}
