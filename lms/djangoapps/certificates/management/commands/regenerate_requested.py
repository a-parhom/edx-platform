import logging
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from optparse import make_option
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

#from badges.events.course_complete import get_completion_badge
from lms.djangoapps.certificates.api import regenerate_user_certificates
from lms.djangoapps.certificates.models import CertificateRegenerationRequest
from xmodule.modulestore.django import modulestore

LOGGER = logging.getLogger(__name__)

class Command(BaseCommand):

    help = """
    Regenerates certificates per course
        $ ... cert_regeneration --course course_id
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="Don't grade or add certificate requests to the queue")

        parser.add_argument('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=False,
                    help='The course id (e.g., mit/6-002x/circuits-and-electronics)')

    def handle(self, *args, **options):   
        LOGGER.info(
            (
                u"Starting to create tasks to regenerate certificates "
                u"with arguments %s and options %s"
            ),
            str(args),
            str(options)
        )

        if options['course']:
            course_id = CourseKey.from_string(options['course'])
        else:
            raise CommandError("You must specify a course")

        requests = CertificateRegenerationRequest.objects.filter(course_id=course_id,
            status='requested')

        for req in requests:
            student = User.objects.get(username=req.user.username, 
                courseenrollment__course_id=course_id)

            course = modulestore().get_course(course_id, depth=2)

            if not options['noop']:
                LOGGER.info(
                    (
                        u"Adding task to the XQueue to generate a certificate "
                        u"for student %s in course '%s'."
                    ),
                    student.id,
                    course_id
                )

		"""
                if course.issue_badges:
                    badge_class = get_completion_badge(course_id, student)
                    badge = badge_class.get_for_user(student)

                    if badge:
                        badge.delete()
                        LOGGER.info(u"Cleared badge for student %s.", student.id)
		"""

                # Add the certificate request to the queue
                ret = regenerate_user_certificates(
                    student, course_id, course=course,
                    forced_grade=None,
                    template_file=None,
                    insecure=None
                )  

                LOGGER.info(
                    (
                        u"Added a certificate regeneration task to the XQueue "
                        u"for student %s in course '%s'. "
                        u"The new certificate status is '%s'."
                    ),
                    student.id,
                    str(course_id),
                    ret
                ) 

                CertificateRegenerationRequest.objects.filter(id=req.id).update(status="regenerated", modified=timezone.now())

            else:
                LOGGER.info(
                    (
                        u"Skipping certificate generation for "
                        u"student %s in course '%s' "
                        u"because the noop flag is set."
                    ),
                    student.id,
                    str(course_id)
                )

            LOGGER.info(
                (
                    u"Finished regenerating certificates command for "
                    u"user %s and course '%s'."
                ),
                student.id,
                str(course_id)
            )
