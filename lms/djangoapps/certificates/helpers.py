# coding=utf-8
"""Helpers for the certificates app. """
import string

from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from .models import CertificateRegenerationRequest, GeneratedCertificate
from student.models import UserProfile

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


def regeneration_request_available(user, course_id):
    """
    Check if certificate regeneration can be requested
    and return the purpose of regeneration if available
    """
    try:
        generated_certificate = GeneratedCertificate.objects.get(  # pylint: disable=no-member
            user=user, course_id=course_id)
        cert_grade = generated_certificate.grade or 0
        cert_name = generated_certificate.name
    except GeneratedCertificate.DoesNotExist:
        return False

    u_prof = UserProfile.objects.get(user=user)
    user_name_changed = (u_prof.name != cert_name)

    changed_names = CertificateRegenerationRequest.objects.filter(user=user,
        course_id=course_id, purpose='name_changed')
    if user_name_changed and len(changed_names)<2:
        if not trigram_check(u_prof.name, cert_name):
            return False
        return 'name_changed'
    elif len(changed_names)>=2:
        return False

    grade = CourseGradeFactory().read(user, course_key=course_id)

    grade_summary_percent = 0
    if grade is not None:
        grade_summary_percent = grade.percent

    if float(grade_summary_percent) > float(cert_grade):
        return 'grade_increased'

    return False


def regeneration_in_progress(user, course_id):
    """
    Check if certificate regeneration has already been requested
    """
    regeneration_is_requested = CertificateRegenerationRequest.objects.filter(user=user,
            course_id=course_id, status='requested')
    if len(regeneration_is_requested)>0:
        return True
    return False
