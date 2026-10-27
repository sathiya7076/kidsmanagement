import os
from datetime import date, datetime, timedelta, time
from PIL import Image, ImageDraw, ImageFont
import qrcode

from app import app, db
from models import (
    User, Child, ActivityLog, Photo,
    Attendance, Message, LearningResource, Complaint, Notification
)

def create_sample_image(filepath, text, bg_color=(255, 230, 200), text_color=(50, 50, 50)):
    """Generate a clean visual placeholder image using Pillow"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    width, height = 600, 400
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(180, 180, 180), width=4)
    
    # Draw accent circle
    draw.ellipse([(width//2 - 60, height//2 - 90), (width//2 + 60, height//2 + 30)], fill=(255, 255, 255))
    
    # Text
    lines = text.split('\n')
    y_start = height // 2 + 50
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y_start + (i * 24)), line, fill=text_color)
        
    img.save(filepath, 'JPEG')

def seed_database():
    with app.app_context():
        print("🌱 Resetting and seeding database...")
        db.drop_all()
        db.create_all()

        photo_dir = app.config['PHOTO_UPLOAD_FOLDER']
        qr_dir = app.config['QR_UPLOAD_FOLDER']
        os.makedirs(photo_dir, exist_ok=True)
        os.makedirs(qr_dir, exist_ok=True)

        # 1. Users
        # Admin
        admin = User(
            name="Admin",
            email="admin@daycare.com",
            role="admin",
            phone="+1 (555) 100-0001",
            is_approved=True
        )
        admin.set_password("Admin123!")

        # Caregiver 1 (Approved)
        caregiver1 = User(
            name="Emma Thompson",
            email="caregiver1@daycare.com",
            role="caregiver",
            phone="+1 (555) 200-0001",
            is_approved=True
        )
        caregiver1.set_password("Caregiver123!")

        # Caregiver 2 (Approved)
        caregiver2 = User(
            name="Marcus Vance",
            email="caregiver2@daycare.com",
            role="caregiver",
            phone="+1 (555) 200-0002",
            is_approved=True
        )
        caregiver2.set_password("Caregiver123!")

        # Caregiver 3 (Pending Approval for admin demo)
        caregiver3 = User(
            name="Jessica Alba",
            email="pending@daycare.com",
            role="caregiver",
            phone="+1 (555) 200-0003",
            is_approved=False
        )
        caregiver3.set_password("Caregiver123!")

        # Parents
        parent1 = User(
            name="David Miller",
            email="parent1@example.com",
            role="parent",
            phone="+1 (555) 300-0001",
            is_approved=True
        )
        parent1.set_password("Parent123!")

        parent2 = User(
            name="Elena Rostova",
            email="parent2@example.com",
            role="parent",
            phone="+1 (555) 300-0002",
            is_approved=True
        )
        parent2.set_password("Parent123!")

        parent3 = User(
            name="James Wilson",
            email="parent3@example.com",
            role="parent",
            phone="+1 (555) 300-0003",
            is_approved=True
        )
        parent3.set_password("Parent123!")

        db.session.add_all([admin, caregiver1, caregiver2, caregiver3, parent1, parent2, parent3])
        db.session.commit()
        print("  ✓ Users created")

        # 2. Children
        today = date.today()

        child1 = Child(
            name="Leo Miller",
            dob=today - timedelta(days=780), # ~2 years old
            gender="male",
            allergies="Peanuts, Strawberries",
            notes="Needs sleep bunny plush for nap time. Very curious, loves watercolor paints.",
            parent_id=parent1.id,
            caregiver_id=caregiver1.id
        )

        child2 = Child(
            name="Sophia Rostova",
            dob=today - timedelta(days=1100), # ~3 years old
            gender="female",
            allergies="None",
            notes="Loves water play, building blocks, and singing nursery rhymes.",
            parent_id=parent2.id,
            caregiver_id=caregiver1.id
        )

        child3 = Child(
            name="Maya Rostova",
            dob=today - timedelta(days=240), # ~8 months old
            gender="female",
            allergies="Lactose sensitivity (use oat formula provided in bag)",
            notes="Infant nursery room. Bottle schedule: 9:30 AM & 1:30 PM. Nap with white noise.",
            parent_id=parent2.id,
            caregiver_id=caregiver2.id
        )

        child4 = Child(
            name="Noah Wilson",
            dob=today - timedelta(days=1500), # ~4 years old
            gender="male",
            allergies="Bee stings (EpiPen in front zipper of emergency backpack)",
            notes="Pre-K learning program. Loves dinosaur stories and building mega towers.",
            parent_id=parent3.id,
            caregiver_id=caregiver2.id
        )

        db.session.add_all([child1, child2, child3, child4])
        db.session.commit()

        # Generate QR codes for children
        for child in [child1, child2, child3, child4]:
            child.generate_qr_code(qr_dir)
        db.session.commit()
        print("  ✓ Children & QR codes generated")

        # 3. Attendance history (Past 30 weekdays)
        print("  ✓ Seeding attendance history...")
        for child in [child1, child2, child3, child4]:
            for d in range(30, 0, -1):
                past_date = today - timedelta(days=d)
                if past_date.weekday() < 5: # Monday to Friday
                    # 90% present, 5% late, 5% absent
                    if d % 14 == 0:
                        status = 'absent'
                        cin, cout = None, None
                        notes = "Family vacation day"
                    elif d % 9 == 0:
                        status = 'late'
                        cin = datetime.combine(past_date, time(9, 35))
                        cout = datetime.combine(past_date, time(16, 45))
                        notes = "Doctor appointment before dropoff"
                    else:
                        status = 'present'
                        cin = datetime.combine(past_date, time(8, 20 + (d % 15)))
                        cout = datetime.combine(past_date, time(16, 30 + (d % 25)))
                        notes = "On time"

                    att = Attendance(
                        child_id=child.id,
                        date=past_date,
                        check_in_time=cin,
                        check_out_time=cout,
                        status=status,
                        marked_by=child.caregiver_id or admin.id,
                        notes=notes
                    )
                    db.session.add(att)

            # Today's attendance (Checked in for today)
            today_att = Attendance(
                child_id=child.id,
                date=today,
                check_in_time=datetime.combine(today, time(8, 30)),
                check_out_time=None, # still checked in!
                status='present',
                marked_by=child.caregiver_id or admin.id,
                notes='Checked in via morning drop-off'
            )
            db.session.add(today_att)
        db.session.commit()

        # 4. Activity Logs (Today and recent days)
        print("  ✓ Seeding activity logs...")
        activities_data = [
            # Leo
            (child1.id, caregiver1.id, 'meal', 'Breakfast: Oatmeal with Berries', 'Ate whole bowl and drank 150ml water.', today, time(8, 45)),
            (child1.id, caregiver1.id, 'mood', 'Mood: Happy & Curious', 'Smiling and engaged during morning greeting circle.', today, time(9, 15)),
            (child1.id, caregiver1.id, 'milestone', 'Finger Painting Milestone', 'Identified primary colors (red, blue, yellow) while painting sunshine.', today, time(10, 30)),
            (child1.id, caregiver1.id, 'diaper', 'Diaper: Wet Changed', 'Clean and dry diaper change before outdoor play.', today, time(11, 15)),
            (child1.id, caregiver1.id, 'meal', 'Lunch: Mac & Cheese with Peas', 'Ate Most of the meal (approx 85%), loved the peas.', today, time(12, 0)),
            (child1.id, caregiver1.id, 'nap', 'Afternoon Nap (12:30 PM - 2:00 PM)', 'Quality: Peaceful rest with sleep bunny toy. Slept 1.5 hours.', today, time(14, 0)),
            (child1.id, caregiver1.id, 'note', 'Health Observation', 'Leo felt a little warm after waking up. Temperature checked: 99.8°F. Alert sent to parent.', today, time(14, 15)),

            # Sophia
            (child2.id, caregiver1.id, 'meal', 'Morning Snack: Apple Slices & Milk', 'Finished all apple slices and cup of milk.', today, time(9, 0)),
            (child2.id, caregiver1.id, 'mood', 'Mood: Playful & Energetic', 'Helped build a wooden castle tower with classmates.', today, time(10, 15)),
            (child2.id, caregiver1.id, 'meal', 'Lunch: Veggie Pasta & Sliced Peaches', 'Ate All portions, asked for a second slice of peach.', today, time(12, 10)),
            (child2.id, caregiver1.id, 'nap', 'Rest Time (12:45 PM - 1:45 PM)', 'Resting quietly listening to storytime music.', today, time(13, 50)),
            (child2.id, caregiver1.id, 'diaper', 'Bathroom: Potty Success', 'Independently asked for the bathroom and washed hands properly!', today, time(14, 20)),

            # Maya
            (child3.id, caregiver2.id, 'meal', 'Morning Bottle: Oat Formula 180ml', 'Took entire bottle gently, burped twice.', today, time(9, 30)),
            (child3.id, caregiver2.id, 'milestone', 'Tummy Time Milestone', 'Held head high for over 4 minutes looking in mirror!', today, time(10, 20)),
            (child3.id, caregiver2.id, 'nap', 'Morning Nap (10:45 AM - 11:45 AM)', 'Fell asleep gently in crib with soft lullaby.', today, time(11, 45)),
            (child3.id, caregiver2.id, 'diaper', 'Diaper: Wet & Soiled Changed', 'Diaper changed with organic rash ointment applied.', today, time(12, 15)),
            (child3.id, caregiver2.id, 'meal', 'Afternoon Bottle: 150ml', 'Drank smoothly, peaceful mood.', today, time(13, 30)),

            # Noah
            (child4.id, caregiver2.id, 'mood', 'Mood: Excited & Enthusiastic', 'Arrived eager to show friends his dinosaur drawing book.', today, time(9, 10)),
            (child4.id, caregiver2.id, 'milestone', 'Reading Milestone', 'Sounded out 4 sight words: "cat", "sun", "play", "tree".', today, time(10, 40)),
            (child4.id, caregiver2.id, 'meal', 'Lunch: Turkey Wrap & Cucumber', 'Ate All food. Enjoyed crunchy cucumbers.', today, time(12, 15)),
            (child4.id, caregiver2.id, 'nap', 'Quiet Book Time (12:45 PM - 1:30 PM)', 'Read through picture book quietly on the floor mat.', today, time(13, 30)),
            (child4.id, caregiver2.id, 'note', 'Outdoor Recess', 'Led a fun tag game on the playground with friends.', today, time(14, 30)),

            # Logs for yesterday for testing date picker
            (child1.id, caregiver1.id, 'meal', 'Lunch: Vegetable Rice & Tofu', 'Ate Most of the bowl.', today - timedelta(days=1), time(12, 15)),
            (child1.id, caregiver1.id, 'nap', 'Nap (12:30 PM - 2:15 PM)', 'Slept soundly for 1h 45m.', today - timedelta(days=1), time(14, 15)),
            (child2.id, caregiver1.id, 'meal', 'Lunch: Grilled Cheese & Tomato Soup', 'Ate All portions.', today - timedelta(days=1), time(12, 20)),
            (child3.id, caregiver2.id, 'meal', 'Afternoon Formula: 180ml', 'Drank all smoothly.', today - timedelta(days=1), time(13, 40)),
            (child4.id, caregiver2.id, 'milestone', 'Lego Tower Milestone', 'Constructed 25-block tower without falling.', today - timedelta(days=1), time(11, 15))
        ]

        for cid, uid, ltype, title, details, ldate, ltime in activities_data:
            ts = datetime.combine(ldate, ltime)
            log = ActivityLog(
                child_id=cid,
                type=ltype,
                title=title,
                details=details,
                logged_by=uid,
                timestamp=ts
            )
            db.session.add(log)
        db.session.commit()

        # 5. Photos
        print("  ✓ Generating sample activity photos...")
        photo_samples = [
            ("uploads/photos/leo_painting.jpg", "Leo enjoying finger painting colors 🎨", "Art", child1.id, caregiver1.id, (255, 220, 200), "Leo's Art Time\nFinger Painting Workshop"),
            ("uploads/photos/sophia_blocks.jpg", "Sophia built a magnificent castle tower! 🏰", "Activity", child2.id, caregiver1.id, (200, 235, 255), "Sophia's Tower\nCreative Building Blocks"),
            ("uploads/photos/maya_tummy.jpg", "Maya smiling big during tummy time ✨", "Milestone", child3.id, caregiver2.id, (230, 255, 220), "Maya's Tummy Time\nSensory Play Session"),
            ("uploads/photos/noah_dino.jpg", "Noah sharing his favorite dinosaur stories 🦕", "Activity", child4.id, caregiver2.id, (255, 245, 200), "Noah Reading Time\nPre-K Story Circle"),
            ("uploads/photos/leo_outdoor.jpg", "Leo playing in the sunny sandbox area ☀️", "Outdoor", child1.id, caregiver1.id, (255, 230, 230), "Sandbox Adventures\nSunny Recess Fun"),
            ("uploads/photos/sophia_music.jpg", "Sophia drumming to the nursery rhyme rhythm 🥁", "Activity", child2.id, caregiver1.id, (240, 230, 255), "Music Circle\nRhythm & Song Play")
        ]

        for rel_path, caption, category, cid, uid, bg_col, banner_text in photo_samples:
            abs_path = os.path.join(app.root_path, 'static', rel_path)
            create_sample_image(abs_path, banner_text, bg_color=bg_col)
            
            p = Photo(
                child_id=cid,
                filepath=rel_path,
                caption=caption,
                category=category,
                uploaded_by=uid,
                timestamp=datetime.utcnow() - timedelta(hours=2)
            )
            db.session.add(p)
        db.session.commit()

        # 6. Messages & Emergency Alert
        print("  ✓ Seeding chat messages & emergency alert...")
        msg1 = Message(
            child_id=child1.id,
            sender_id=parent1.id,
            receiver_id=caregiver1.id,
            content="Good morning Emma! Leo was a little fussy this morning because of teething, just wanted to let you know.",
            timestamp=datetime.utcnow() - timedelta(hours=5),
            is_alert=False
        )
        msg2 = Message(
            child_id=child1.id,
            sender_id=caregiver1.id,
            receiver_id=parent1.id,
            content="Good morning David! Thank you so much for the update. We have his chilled teething ring ready and will give him extra cuddles.",
            timestamp=datetime.utcnow() - timedelta(hours=4, minutes=45),
            is_alert=False
        )
        msg3 = Message(
            child_id=child1.id,
            sender_id=parent1.id,
            receiver_id=caregiver1.id,
            content="Wonderful! I will be picking him up at 4:30 PM today.",
            timestamp=datetime.utcnow() - timedelta(hours=3),
            is_alert=False
        )
        
        # High-priority Emergency Alert for Leo
        alert_msg = Message(
            child_id=child1.id,
            sender_id=caregiver1.id,
            receiver_id=parent1.id,
            content="🚨 [MILD FEVER CHECK] - Leo felt warm after nap time. We measured his temperature at 99.8°F. He is drinking cool water and resting comfortably with his bunny plush, but please monitor closely upon pickup at 4:30 PM.",
            timestamp=datetime.utcnow() - timedelta(minutes=45),
            is_alert=True,
            alert_severity="warning"
        )

        db.session.add_all([msg1, msg2, msg3, alert_msg])
        db.session.commit()

        # 7. Notifications
        print("  ✓ Seeding notifications...")
        n1 = Notification(
            user_id=parent1.id,
            title="🚨 Child Health Alert: Leo Miller",
            message="Leo has a mild temperature of 99.8°F. Staff is attending to him.",
            link=f"/messages/{child1.id}",
            is_urgent=True,
            is_read=False
        )
        n2 = Notification(
            user_id=parent1.id,
            title="📸 New Photo of Leo",
            message="Emma Thompson uploaded a new photo: Finger Painting Workshop.",
            link=f"/parent/child/{child1.id}/photos",
            is_urgent=False,
            is_read=False
        )
        n3 = Notification(
            user_id=parent2.id,
            title="Potty Success for Sophia!",
            message="Sophia independently used the bathroom today!",
            link=f"/parent/child/{child2.id}/timeline",
            is_urgent=False,
            is_read=False
        )
        n4 = Notification(
            user_id=admin.id,
            title="Caregiver Registration Pending",
            message="Jessica Alba registered as a caregiver and is waiting for approval.",
            link="/admin/caregivers",
            is_urgent=False,
            is_read=False
        )
        db.session.add_all([n1, n2, n3, n4])
        db.session.commit()

        # 8. Learning Resources
        print("  ✓ Seeding interactive learning resources...")
        resources = [
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
How I wonder what you are!

When the blazing sun is gone,
When he nothing shines upon,
Then you show your little light,
Twinkle, twinkle, through the night.""",
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
                title="The Three Little Pigs",
                type="story",
                age_group="preschool",
                category="Language & Imagination",
                description="Classic fairy tale encouraging resilience, dedication, and problem-solving.",
                content_url_or_text="""Once upon a time, three little pigs set out to build homes of their own.

The first little pig built his house out of straw because it was quick and easy.
The second little pig built his house out of sticks.
The third little pig took his time and built his house out of sturdy red bricks.

Soon, the big bad wolf came knocking:
"Little pig, little pig, let me come in!"
"Not by the hair of my chinny chin chin!"
"Then I'll huff, and I'll puff, and I'll blow your house down!"

With a mighty gust, the straw and stick houses tumbled, and the two pigs dashed safely to their brother's brick house!
The wolf huffed and puffed, but the brick house stood strong.
The three pigs danced with joy, knowing that careful craftsmanship always pays off!""",
                icon="bi-journal-bookmark"
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
            ),
            LearningResource(
                title="Simon Says: Animal Movement Edition",
                type="game",
                age_group="preschool",
                category="Gross Motor & Listening",
                description="A high-energy listening game that gets kids hopping, crawling, and stretching!",
                content_url_or_text="""Game Rules:
- When the leader says "Simon says...", children perform the action!
- If the leader doesn't say "Simon says", freeze!

Fun Movements:
- "Simon says: Hop like a kangaroo!" (Jump with both feet)
- "Simon says: Flap your wings like an eagle!" (Stretch arms wide)
- "Simon says: Slither like a gentle snake!" (Slow wiggle)
- "Simon says: Stand tall like a flamingo on one leg!" (Balance practice)
- "Roar like a lion!" (Freeze test - don't move unless Simon says!)""",
                icon="bi-controller"
            )
        ]

        db.session.add_all(resources)
        db.session.commit()

        # 9. Complaints / Inquiries
        print("  ✓ Seeding parent complaints & inquiries...")
        c1 = Complaint(
            user_id=parent2.id,
            child_id=child2.id,
            subject="Question regarding outdoor sun protection policy",
            message="Hi Admin, with the upcoming warmer weather, do we send sunscreen from home with child's name, or does the daycare supply organic SPF for outdoor play?",
            status="open",
            created_at=datetime.utcnow() - timedelta(hours=6)
        )
        c2 = Complaint(
            user_id=parent3.id,
            child_id=child4.id,
            subject="Late pickup fee schedule inquiry",
            message="Hello, I wanted to verify the procedure if work traffic delays pickup past 5:30 PM.",
            status="resolved",
            admin_response="Hello James, we offer a 15-minute grace period until 5:45 PM if you send a message in advance through the portal. After that, standard overtime staff compensation of $15/15mins applies.",
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add_all([c1, c2])
        db.session.commit()

        print("\n✨ Seeding completed successfully!")
        print("="*60)
        print("DEFAULT CREDENTIALS FOR TESTING:")
        print("  1. Admin:       admin@daycare.com       / Admin123!")
        print("  2. Caregiver 1: caregiver1@daycare.com   / Caregiver123! (Emma Thompson - Approved)")
        print("  3. Caregiver 2: caregiver2@daycare.com   / Caregiver123! (Marcus Vance - Approved)")
        print("  4. Caregiver 3: pending@daycare.com      / Caregiver123! (Jessica Alba - Pending Approval)")
        print("  5. Parent 1:    parent1@example.com      / Parent123! (David Miller - Father of Leo)")
        print("  6. Parent 2:    parent2@example.com      / Parent123! (Elena Rostova - Mother of Sophia & Maya)")
        print("  7. Parent 3:    parent3@example.com      / Parent123! (James Wilson - Father of Noah)")
        print("="*60)

if __name__ == '__main__':
    seed_database()
