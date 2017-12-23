# coding=utf-8
"""Helpers for the student app. """
from datetime import datetime
import urllib

from pytz import UTC
from django.core.urlresolvers import reverse, NoReverseMatch

import third_party_auth
from lms.djangoapps.verify_student.models import VerificationDeadline, SoftwareSecurePhotoVerification
from course_modes.models import CourseMode

import string


# Enumeration of per-course verification statuses
# we display on the student dashboard.
VERIFY_STATUS_NEED_TO_VERIFY = "verify_need_to_verify"
VERIFY_STATUS_SUBMITTED = "verify_submitted"
VERIFY_STATUS_APPROVED = "verify_approved"
VERIFY_STATUS_MISSED_DEADLINE = "verify_missed_deadline"
VERIFY_STATUS_NEED_TO_REVERIFY = "verify_need_to_reverify"

DISABLE_UNENROLL_CERT_STATES = [
    'generating',
    'ready',
]


def check_verify_status_by_course(user, course_enrollments):
    """
    Determine the per-course verification statuses for a given user.

    The possible statuses are:
        * VERIFY_STATUS_NEED_TO_VERIFY: The student has not yet submitted photos for verification.
        * VERIFY_STATUS_SUBMITTED: The student has submitted photos for verification,
          but has have not yet been approved.
        * VERIFY_STATUS_APPROVED: The student has been successfully verified.
        * VERIFY_STATUS_MISSED_DEADLINE: The student did not submit photos within the course's deadline.
        * VERIFY_STATUS_NEED_TO_REVERIFY: The student has an active verification, but it is
            set to expire before the verification deadline for the course.

    It is is also possible that a course does NOT have a verification status if:
        * The user is not enrolled in a verified mode, meaning that the user didn't pay.
        * The course does not offer a verified mode.
        * The user submitted photos but an error occurred while verifying them.
        * The user submitted photos but the verification was denied.

    In the last two cases, we rely on messages in the sidebar rather than displaying
    messages for each course.

    Arguments:
        user (User): The currently logged-in user.
        course_enrollments (list[CourseEnrollment]): The courses the user is enrolled in.

    Returns:
        dict: Mapping of course keys verification status dictionaries.
            If no verification status is applicable to a course, it will not
            be included in the dictionary.
            The dictionaries have these keys:
                * status (str): One of the enumerated status codes.
                * days_until_deadline (int): Number of days until the verification deadline.
                * verification_good_until (str): Date string for the verification expiration date.

    """
    status_by_course = {}

    # Retrieve all verifications for the user, sorted in descending
    # order by submission datetime
    verifications = SoftwareSecurePhotoVerification.objects.filter(user=user)

    # Check whether the user has an active or pending verification attempt
    # To avoid another database hit, we re-use the queryset we have already retrieved.
    has_active_or_pending = SoftwareSecurePhotoVerification.user_has_valid_or_pending(
        user, queryset=verifications
    )

    # Retrieve verification deadlines for the enrolled courses
    enrolled_course_keys = [enrollment.course_id for enrollment in course_enrollments]
    course_deadlines = VerificationDeadline.deadlines_for_courses(enrolled_course_keys)

    recent_verification_datetime = None

    for enrollment in course_enrollments:

        # If the user hasn't enrolled as verified, then the course
        # won't display state related to its verification status.
        if enrollment.mode in CourseMode.VERIFIED_MODES:

            # Retrieve the verification deadline associated with the course.
            # This could be None if the course doesn't have a deadline.
            deadline = course_deadlines.get(enrollment.course_id)

            relevant_verification = SoftwareSecurePhotoVerification.verification_for_datetime(deadline, verifications)

            # Picking the max verification datetime on each iteration only with approved status
            if relevant_verification is not None and relevant_verification.status == "approved":
                recent_verification_datetime = max(
                    recent_verification_datetime if recent_verification_datetime is not None
                    else relevant_verification.expiration_datetime,
                    relevant_verification.expiration_datetime
                )

            # By default, don't show any status related to verification
            status = None

            # Check whether the user was approved or is awaiting approval
            if relevant_verification is not None:
                if relevant_verification.status == "approved":
                    status = VERIFY_STATUS_APPROVED
                elif relevant_verification.status == "submitted":
                    status = VERIFY_STATUS_SUBMITTED

            # If the user didn't submit at all, then tell them they need to verify
            # If the deadline has already passed, then tell them they missed it.
            # If they submitted but something went wrong (error or denied),
            # then don't show any messaging next to the course, since we already
            # show messages related to this on the left sidebar.
            submitted = (
                relevant_verification is not None and
                relevant_verification.status not in ["created", "ready"]
            )
            if status is None and not submitted:
                if deadline is None or deadline > datetime.now(UTC):
                    if has_active_or_pending:
                        # The user has an active verification, but the verification
                        # is set to expire before the deadline.  Tell the student
                        # to reverify.
                        status = VERIFY_STATUS_NEED_TO_REVERIFY
                    else:
                        status = VERIFY_STATUS_NEED_TO_VERIFY
                else:
                    # If a user currently has an active or pending verification,
                    # then they may have submitted an additional attempt after
                    # the verification deadline passed.  This can occur,
                    # for example, when the support team asks a student
                    # to reverify after the deadline so they can receive
                    # a verified certificate.
                    # In this case, we still want to show them as "verified"
                    # on the dashboard.
                    if has_active_or_pending:
                        status = VERIFY_STATUS_APPROVED

                    # Otherwise, the student missed the deadline, so show
                    # them as "honor" (the kind of certificate they will receive).
                    else:
                        status = VERIFY_STATUS_MISSED_DEADLINE

            # Set the status for the course only if we're displaying some kind of message
            # Otherwise, leave the course out of the dictionary.
            if status is not None:
                days_until_deadline = None

                now = datetime.now(UTC)
                if deadline is not None and deadline > now:
                    days_until_deadline = (deadline - now).days

                status_by_course[enrollment.course_id] = {
                    'status': status,
                    'days_until_deadline': days_until_deadline
                }

    if recent_verification_datetime:
        for key, value in status_by_course.iteritems():  # pylint: disable=unused-variable
            status_by_course[key]['verification_good_until'] = recent_verification_datetime.strftime("%m/%d/%Y")

    return status_by_course


def auth_pipeline_urls(auth_entry, redirect_url=None):
    """Retrieve URLs for each enabled third-party auth provider.

    These URLs are used on the "sign up" and "sign in" buttons
    on the login/registration forms to allow users to begin
    authentication with a third-party provider.

    Optionally, we can redirect the user to an arbitrary
    url after auth completes successfully.  We use this
    to redirect the user to a page that required login,
    or to send users to the payment flow when enrolling
    in a course.

    Args:
        auth_entry (string): Either `pipeline.AUTH_ENTRY_LOGIN` or `pipeline.AUTH_ENTRY_REGISTER`

    Keyword Args:
        redirect_url (unicode): If provided, send users to this URL
            after they successfully authenticate.

    Returns:
        dict mapping provider IDs to URLs

    """
    if not third_party_auth.is_enabled():
        return {}

    return {
        provider.provider_id: third_party_auth.pipeline.get_login_url(
            provider.provider_id, auth_entry, redirect_url=redirect_url
        ) for provider in third_party_auth.provider.Registry.accepting_logins()
    }


# Query string parameters that can be passed to the "finish_auth" view to manage
# things like auto-enrollment.
POST_AUTH_PARAMS = ('course_id', 'enrollment_action', 'course_mode', 'email_opt_in', 'purchase_workflow')


def get_next_url_for_login_page(request):
    """
    Determine the URL to redirect to following login/registration/third_party_auth

    The user is currently on a login or registration page.
    If 'course_id' is set, or other POST_AUTH_PARAMS, we will need to send the user to the
    /account/finish_auth/ view following login, which will take care of auto-enrollment in
    the specified course.

    Otherwise, we go to the ?next= query param or to the dashboard if nothing else is
    specified.
    """
    redirect_to = request.GET.get('next', None)
    if not redirect_to:
        try:
            redirect_to = reverse('dashboard')
        except NoReverseMatch:
            redirect_to = reverse('home')
    if any(param in request.GET for param in POST_AUTH_PARAMS):
        # Before we redirect to next/dashboard, we need to handle auto-enrollment:
        params = [(param, request.GET[param]) for param in POST_AUTH_PARAMS if param in request.GET]
        params.append(('next', redirect_to))  # After auto-enrollment, user will be sent to payment page or to this URL
        redirect_to = '{}?{}'.format(reverse('finish_auth'), urllib.urlencode(params))
        # Note: if we are resuming a third party auth pipeline, then the next URL will already
        # be saved in the session as part of the pipeline state. That URL will take priority
        # over this one.
    return redirect_to


def trigram_check(s1, s2):
    """
    Needed to check how different is the name on the issued certificate compared to the name in the user profile
    Used when request for certificate regeneration is being made
    """
    def _is_ascii(s):
        try:
            s.encode('ascii')
        except UnicodeEncodeError:
            return False
        else:
            return True


    def _lat2cyr(s):
        i = 0
        sb = ''
        while i < len(s):
            ch = s[i]
            if i == 0:
                ch = ch.upper()

                if ch == 'Y': 
                    if i+1 < len(s) and s[i+1].upper()=='A':
                        sb += u'Я'
                        i+=1
                    elif i+1 < len(s) and s[i+1].upper()=='U':
                        sb += u'Ю'
                        i+=1
                    elif i+1 < len(s) and s[i+1].upper()=='E':
                        sb += u'Є'
                        i+=1
                    elif i+1 < len(s) and s[i+1].upper()=='I':
                        sb += u'Ї'
                        i+=1
                    else:
                        sb += u'Й'
                elif ch == 'T':
                    if i+1 < len(s) and s[i+1].upper()=='s':
                        sb += u'Ц'
                        i+=1
                    else:
                        sb += u'Т'
                elif i+1 < len(s) and s[i+1].upper()=='H' and ch in ['Z','K','C','S'] :
                    if ch == 'Z': 
                        sb += u'Ж'
                        i+=1
                    elif ch == 'K': 
                        sb += u'Х'
                        i+=1
                    elif ch == 'C': 
                        sb += u'Ч'
                        i+=1
                    elif ch == 'S':
                        if i+3 < len(s) and s[i+3].upper() =='H': 
                            sb += u'Щ'
                            i+=3 
                        else:
                            sb += u'Ш'
                            i+=1
                else: 
                    if ch =='A':
                        sb += u'А'
                    if ch == 'B':
                        sb += u'Б'
                    if ch == 'V':
                        sb += u'В'
                    if ch == 'H':
                        sb += u'Г'
                    if ch == 'G':
                        sb += u'Ґ'
                    if ch == 'D':
                        sb += u'Д'
                    if ch == 'E':
                        sb += u'Е'
                    if ch == 'Z':
                        sb += u'З'
                    if ch == 'K':
                        sb += u'К'
                    if ch == 'L':
                        sb += u'Л'
                    if ch == 'M':
                        sb += u'М'
                    if ch == 'N':
                        sb += u'Н'
                    if ch == 'O':
                        sb += u'О'
                    if ch == 'P':
                        sb += u'П'
                    if ch == 'R':
                        sb += u'Р'
                    if ch == 'S':
                        sb += u'С'
                    if ch == 'U':
                        sb += u'У'
                    if ch == 'F':
                        sb += u'Ф'
            else:
                ch = ch.lower()

                if ch == 'i': 
                    if i+1 < len(s) and s[i+1].lower()=='a':
                        sb += u'я'
                        i+=1
                    elif i+1 < len(s) and s[i+1].lower()=='u':
                        sb += u'ю'
                        i+=1
                    elif i+1 < len(s) and s[i+1].lower()=='e':
                        sb += u'є'
                        i+=1
                    elif i-1 >= 0 and s[i-1].lower()=='i':
                        sb += u'й'
                        i+=1
                    else:
                        sb += u'і'
                elif ch == 't':
                    if i+1 < len(s) and s[i+1].lower()=='s':
                        sb += u'ц'
                        i+=1
                    else:
                        sb += u'т'
                elif i+1 < len(s) and s[i+1].lower()=='h' and ch in ['z','k','c','s'] :
                    if ch == 'z': 
                        sb += u'ж'
                        i+=1
                    elif ch == 'k': 
                        sb += u'х'
                        i+=1
                    elif ch == 'c': 
                        sb += u'ч'
                        i+=1
                    elif ch == 's':
                        if i+3 < len(s) and s[i+3].lower() =='h': 
                            sb += u'щ'
                            i+=3 
                        else:
                            sb += u'ш'
                else: 
                    if ch =='a':
                        sb += u'а'
                    if ch == 'b':
                        sb += u'б'
                    if ch == 'v':
                        sb += u'в'
                    if ch == 'h':
                        sb += u'х'
                    if ch == 'g':
                        sb += u'ґ'
                    if ch == 'd':
                        sb += u'д'
                    if ch == 'e':
                        sb += u'е'
                    if ch == 'z':
                        sb += u'з'
                    if ch == 'k':
                        sb += u'к'
                    if ch == 'l':
                        sb += u'л'
                    if ch == 'm':
                        sb += u'м'
                    if ch == 'n':
                        sb += u'н'
                    if ch == 'o':
                        sb += u'о'
                    if ch == 'p':
                        sb += u'п'
                    if ch == 'r':
                        sb += u'р'
                    if ch == 's':
                        sb += u'с'
                    if ch == 'u':
                        sb += u'у'
                    if ch == 'y':
                        sb += u'и'
                    if ch == 'f':
                        sb += u'ф'
            i+=1 
        return sb


    def _prepare_string(input_string):
        # Sanitize string
        output_string = ''.join([char for char in input_string 
            if char not in string.punctuation 
            and not char.isdigit()]).replace(" ","")

        if _is_ascii(output_string):
            output_string = _lat2cyr(output_string)

        return '_'+output_string.lower()+'_'


    def _get_trigrams(input_string):
        trigrams = []
        i = 0

        for char in input_string:
            if i < len(input_string)-2:
                trigrams.append(char+input_string[i+1]+input_string[i+2])
            else: 
                break
            i+=1

        return trigrams 

    """
    # Remove identical words from strings
    words1 = s1.split(" ")
    words2 = s2.split(" ")

    for word1 in words1:
        for word2 in words2:
            if word1 == word2:
                s1 = s1.replace(word1,"")
                s2 = s2.replace(word2,"")
    """

    # Do other preparations
    s1 = _prepare_string(s1)
    s2 = _prepare_string(s2)

    if s1 == s2:
        return True

    s1_trigrams = _get_trigrams(s1)
    s2_trigrams = _get_trigrams(s2)

    a, b, c = len(s1_trigrams), len(s2_trigrams), 0.0

    """
    if a == 0 or b == 0:
        return True
    """

    for trigram in s1_trigrams:
        if trigram in s2_trigrams:
            c += 1

    return ( c / (a + b - c) ) > 0.2