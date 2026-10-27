import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Ensure virtual-daycare is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv()

from app import create_app, db
from models import User, LearningResource

def init_production_db():
    app, socketio = create_app()

    with app.app_context():
        print("🔧 Initializing Production Database...")
        db.create_all()

        # Clean uploads
        photo_dir = app.config['PHOTO_UPLOAD_FOLDER']
        qr_dir = app.config['QR_UPLOAD_FOLDER']
        os.makedirs(photo_dir, exist_ok=True)
        os.makedirs(qr_dir, exist_ok=True)

        # Clear existing sample users, children, logs, photos, messages, attendance, complaints
        # but keep or seed the essential Director admin account and standard learning curriculum
        from models import Child, ActivityLog, Photo, Attendance, Message, Complaint, Notification
        Notification.query.delete()
        Complaint.query.delete()
        Message.query.delete()
        Attendance.query.delete()
        Photo.query.delete()
        ActivityLog.query.delete()
        Child.query.delete()
        User.query.delete()
        db.session.commit()

        # Clean upload files
        for folder in [photo_dir, qr_dir]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        pass

        # Create Director Admin Account
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@daycare.com').strip().lower()
        admin_password = os.environ.get('ADMIN_PASSWORD', 'AdminSecure2026!')
        admin_name = os.environ.get('ADMIN_NAME', 'Admin')
        admin_phone = os.environ.get('DAYCARE_PHONE', '+1 (555) 234-5678')

        admin = User(
            name=admin_name,
            email=admin_email,
            role="admin",
            phone=admin_phone,
            is_approved=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)

        # Seed Standard Curriculum Learning Resources
        LearningResource.query.delete()
        db.session.commit()

        curriculum = [
            LearningResource(
                title="The Itsy Bitsy Spider",
                type="rhyme",
                age_group="infant",
                category="Music & Movement",
                description="A classic fingerplay rhyme teaching hand-eye coordination and rhythm.",
                content_url_or_text="""The itsy bitsy spider climbed up the waterspout.
Down came the rain and washed the spider out.
Out came the sun and dried up all the rain,
And the itsy bitsy spider climbed up the spout again!

Gesture Guide:
1. Touch index finger to thumb in alternating climbing motions.
2. Wiggle fingers downward for falling rain.
3. Form a large circle over head for the warm sun.
4. Climb fingers upward again!""",
                icon="bi-music-note-beamed"
            ),
            LearningResource(
                title="Twinkle, Twinkle, Little Star",
                type="rhyme",
                age_group="all",
                category="Music & Movement",
                description="Calming lullaby rhyme perfect for rest time or gentle circle song.",
                content_url_or_text="""Twinkle, twinkle, little star,
How I wonder what you are!
Up above the world so high,
Like a diamond in the sky.

Twinkle, twinkle, little star,
How I wonder what you are!""",
                icon="bi-star"
            ),
            LearningResource(
                title="The Little Red Hen",
                type="story",
                age_group="toddler",
                category="Social & Emotional",
                description="An interactive story emphasizing cooperation, teamwork, and effort.",
                content_url_or_text="""Once upon a time, there was a hardworking Little Red Hen who lived on a farm with a lazy Dog, a sleepy Cat, and a noisy Duck.

One sunny day, she discovered grains of wheat.
"Who will help me plant this wheat?" asked the Little Red Hen.
"Not I," barked the Dog.
"Not I," purred the Cat.
"Not I," quacked the Duck.
"Then I will plant it myself," said the Little Red Hen. And she did!

The wheat grew tall and golden.
"Who will help me take the wheat to the mill to grind into flour?"
"Not I," said the Dog, Cat, and Duck.
"Then I will do it myself," said the Hen.

She baked a warm, aromatic loaf of fresh bread.
"Now, who will help me eat this bread?"
"I will!" shouted the Dog.
"I will!" purred the Cat.
"I will!" quacked the Duck.

"Oh no you will not," chuckled the Little Red Hen. "My chicks and I worked hard, and we will enjoy this delicious bread together!"

Discussion Points:
- How can we help our friends clean up toys?
- Why is it good to share work before sharing treats?""",
                icon="bi-book"
            ),
            LearningResource(
                title="Sensory Ice & Warm Water Exploration",
                type="activity",
                age_group="toddler",
                category="Sensory & Science",
                description="Hands-on sensory bin activity exploring temperature differences and melting.",
                content_url_or_text="""Activity Materials:
- Shallow plastic tub or sensory tray
- Ice cubes (tinted with safe food coloring: blue and yellow)
- Warm water cups or squirt droppers
- Large spoons and silicone scoops

Steps:
1. Place colorful ice cubes inside the dry sensory tub.
2. Encourage toddler to touch and describe the sensation ("cold, smooth, slippery").
3. Provide warm water in droppers to melt the ice cubes.
4. Observe the colors mixing (yellow + blue = green!).
5. Talk about how temperature turns solid ice into liquid water.""",
                icon="bi-droplet"
            ),
            LearningResource(
                title="Rainbow Color Sorting Game",
                type="activity",
                age_group="preschool",
                category="Math & Logic",
                description="Develops classification skills, hand dexterity, and color vocabulary.",
                content_url_or_text="""Materials:
- Colored cups or bowls (Red, Blue, Green, Yellow, Orange)
- Matching colored pom-poms, blocks, or buttons
- Kid-friendly plastic tweezers or tongs

How to Play:
1. Arrange the cups in a rainbow arch.
2. Scatter the mixed items on the table.
3. Challenge the child to sort items by color using their fingers or tweezers.
4. Count how many items ended up in each cup!
5. Extension: Ask which cup has the MOST or LEAST items.""",
                icon="bi-palette"
            ),
            LearningResource(
                title="Tummy Time Mirror Exploration",
                type="activity",
                age_group="infant",
                category="Motor & Visual Skills",
                description="Engages baby's neck and back muscles while fostering self-awareness.",
                content_url_or_text="""Activity Setup:
- Soft play mat on the carpet
- Shatterproof baby-safe mirror placed vertically at eye level
- High-contrast textured toys (black, white, red)

Instructions:
1. Gently place baby on their tummy with arms forward.
2. Angle the mirror so they can see their own smiling reflection.
3. Make gentle silly faces and talk softly to encourage head lifting.
4. Keep sessions short (3 to 5 minutes) and always closely supervised.
5. Reward with a soothing back rub and warm smiles!""",
                icon="bi-person-badge"
            )
        ]

        db.session.add_all(curriculum)
        db.session.commit()

        print("\n✅ Production Database Initialized Cleanly!")
        print("="*60)
        print("INITIAL DIRECTOR ADMINISTRATOR ACCOUNT:")
        print(f"  Email:    {admin_email}")
        print(f"  Password: {admin_password}")
        print("  Status:   Approved / Active")
        print("="*60)
        print("No sample parents, children, or caregivers are present.")
        print("Ready for live user onboarding and student enrollment.\n")

if __name__ == '__main__':
    init_production_db()
