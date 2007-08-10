#!/usr/bin/env python
# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Email screenshot problem reports to factory administrators.

It's a good idea to run this daily, e.g. by adding a symlink to this
file in /etc/cron.daily.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'shotserver04.settings'
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from shotserver04 import settings
from shotserver04.factories.models import Factory, ScreenSize, ColorDepth
from shotserver04.browsers.models import Browser
from shotserver04.screenshots.models import Screenshot, ProblemReport
from shotserver04.common.templatetags import human

DEBUG = True
HOURS = 3 * 24
PREFIX = 'http://' + Site.objects.all()[0].domain
MAX_EXAMPLES = 3
MAX_ORPHANS = 2


def all_reports(problems):
    for problem in problems:
        yield ''
        yield '%s (Code %d)' % (problem.message, problem.code)
        yield PREFIX + problem.screenshot.get_absolute_url()


def example_urls(problems):
    urls = set([problem.screenshot.get_absolute_url() for problem in problems])
    yield ''
    yield '%s (Code %d)' % (problems[0].message, problems[0].code)
    orphans = len(problems) - MAX_EXAMPLES
    if orphans > MAX_ORPHANS:
        orphans = 0
    for problem in problems[:MAX_EXAMPLES + orphans]:
        yield PREFIX + problem.screenshot.get_absolute_url()
    if len(problems) > MAX_EXAMPLES + orphans:
        yield "... (%d more)" % (len(problems) - MAX_EXAMPLES - orphans)


for factory in Factory.objects.all():
    problems = ProblemReport.objects.filter(
        screenshot__factory=factory,
        reported__gte=datetime.now() - timedelta(hours=HOURS))
    if not len(problems):
        continue
    codes = {}
    for problem in problems:
        if not problem.code in codes:
            codes[problem.code] = []
        codes[problem.code].append(problem)
    body = [u"Hi %s," % factory.admin.first_name, '',
            u"This is an automated user feedback report from Browsershots 0.4."]
    if len(problems) == 1:
        body.append(u"In the last %d hours, there was one %s for" % (
            HOURS, ProblemReport._meta.verbose_name))
    else:
        body.append(u"In the last %d hours, there were %d %s for" % (
            HOURS, len(problems), ProblemReport._meta.verbose_name_plural))
    body.append(PREFIX + factory.get_absolute_url())
    keys = codes.keys()
    keys.sort()
    for code in keys:
        if code == 999:
            body.extend(all_reports(codes[code]))
        else:
            body.extend(example_urls(codes[code]))
    body.extend(['', "Thanks for your time,", "Browsershots"])
    subject = "Problem report for screenshot factory %s" % factory.name
    body = '\n'.join(body)
    from_email = u'%s <%s>' % settings.ADMINS[0]
    recipient_list=[u'%s %s <%s>' % (
        factory.admin.first_name, factory.admin.last_name,
        factory.admin.email)]
    if DEBUG:
        print '=' * len(subject)
        print 'From:', from_email.encode('utf-8')
        print 'To:', u', '.join(recipient_list).encode('utf-8')
        print subject
        print '=' * len(subject)
        print body
    else:
        recipient_list = ['Test R. Boy <test@jogg.de>']
        send_mail(subject, body, from_email, recipient_list)
        #to=factory.admin.email,
        #bcc='johann@browsershots.org')
