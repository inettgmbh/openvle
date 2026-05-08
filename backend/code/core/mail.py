from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template
from sqlalchemy import inspect as sa_inspect

from models import User

from .config import Settings
from .exceptions import MailGenerationError
from .mariadb import SessionLocal

settings = Settings()


# Construct mail
def mail_construct(
    to_mail: str,
    subject: str,
    content_plain: str,
    content_html: str = "",
    context_objects: list | None = None,
    from_name: str = settings.smtp_from_name,
    from_mail: str = settings.smtp_from_mail,
    reply_to: str | None = None,
):
    # Enable multipart message
    msg = MIMEMultipart("alternative")
    # Check for from_name, and set from_mail
    if from_name:
        msg["From"] = str(from_name) + "<" + str(from_mail) + ">"
    else:
        msg["From"] = str(from_mail)
    # Define to mail
    msg["To"] = str(to_mail)
    if reply_to:
        msg["Reply-To"] = str(reply_to)

    # Get recipient user object based on to_mail
    db = SessionLocal()
    user_object = db.query(User).filter(User.email == to_mail).first()
    if not user_object:
        user_object = User(email=to_mail, username="unknown", name="unknown")
    # Base mail context
    context = {
        "user": {
            "username": user_object.username,
            "email": user_object.email,
            "name": user_object.name,
        },
        "project": {
            "name": settings.project_name,
            "title": settings.project_title,
        },
    }
    # Generate additional context data if any context_objects were provided
    if context_objects:
        for obj in context_objects:
            # Eager load object
            obj = db.merge(obj)
            class_name = obj.__class__.__name__
            # Do not include User objects in context (user details are already included)
            if class_name == "User":
                pass
            # Convert object into a dictionary (only column attrs to avoid triggering lazy relationships)
            column_attrs = [
                c.key for c in sa_inspect(obj.__class__).column_attrs
            ]
            obj_dict = {attr: getattr(obj, attr) for attr in column_attrs}
            # Add object as dictionary to context (callable as the lowercase string of class_name)
            context[class_name.lower()] = obj_dict
    # Render the subject
    msg["Subject"] = subject

    # Attach parts into message container.
    # Render the plain text
    try:
        content_plain = Template(content_plain).render(context)
        msg.attach(MIMEText(str(content_plain), "plain"))
        # Render the html text
        if content_html:
            content_html = Template(content_html).render(context)
            msg.attach(MIMEText(str(content_html), "html"))
    except Exception as e:
        raise MailGenerationError(message=str(e))
    finally:
        db.close()
    return msg
