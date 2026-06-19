import sys
import os
import mysql.connector

# Add workspace root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import get_db, execute_query, fetch_all, fetch_one
from auth_utils import hash_password

# List of 100 realistic unique female names
FEMALE_NAMES = [
    # C406 specific names
    "Rashvi", "Aaslin", "Charu Harinee", "Yamini",
    # 90 other realistic unique names
    "Ananya", "Aishwarya", "Priyanka", "Deepika", "Shruti", "Sruthi", "Aditi", "Riya", "Sneha", "Kavya",
    "Divya", "Neha", "Pooja", "Meera", "Swati", "Nisha", "Shreya", "Kirti", "Preeti", "Sonia",
    "Amrita", "Anjali", "Ritu", "Harini", "Swetha", "Nivedita", "Pavithra", "Gayathri", "Sandhya", "Radhika",
    "Priya", "Malini", "Kiran", "Archana", "Sujatha", "Vimala", "Lakshmi", "Saraswathi", "Rajeswari", "Uma",
    "Indira", "Geetha", "Sita", "Gita", "Lata", "Asha", "Usha", "Shanti", "Savitri", "Janaki",
    "Renu", "Bina", "Anita", "Sunita", "Mamta", "Rekha", "Babita", "Komal", "Kiran", "Jyoti",
    "Poonam", "Varsha", "Meena", "Seema", "Alka", "Aruna", "Manju", "Pushpa", "Chitra", "Lalitha",
    "Madhavi", "Shubha", "Roopa", "Kala", "Sona", "Sheela", "Leela", "Maya", "Tara", "Gouri",
    "Bhavana", "Divyanshi", "Ishika", "Khushi", "Mansi", "Prisha", "Riddhima", "Saumya", "Tanisha", "Vaidehi",
    "Aaradhya", "Anushka", "Avani", "Diya", "Gargi", "Ira", "Jahnvi", "Kriti", "Navya", "Rhea"
]

# Ensure names list is unique (except the few we know)
unique_names = []
for name in FEMALE_NAMES:
    if name not in unique_names:
        unique_names.append(name)
        
# Make sure we have enough unique names
while len(unique_names) < 95:
    unique_names.append(f"Student_{len(unique_names)}")

# C406 details
C406_STUDENTS = [
    {"name": "Rashvi", "dept": "AIDS", "year": 4},
    {"name": "Aaslin", "dept": "IT", "year": 4},
    {"name": "Charu Harinee", "dept": "CSE", "year": 4},
    {"name": "Yamini", "dept": "AIML", "year": 4}
]

app = create_app()

def run_migration():
    print("Starting Female Student Data Migration...")
    
    with app.app_context():
        # 1. Alter check constraint chk_student_dept to include 'AIML'
        try:
            execute_query("ALTER TABLE students DROP CONSTRAINT chk_student_dept")
            print("Dropped old constraint chk_student_dept.")
        except Exception as e:
            print("Note: Could not drop constraint (might not exist or already dropped):", e)
            
        try:
            execute_query("""
                ALTER TABLE students ADD CONSTRAINT chk_student_dept 
                CHECK (department IN ('CSE', 'AIDS', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL', 'MBA', 'MCA', 'AIML'))
            """)
            print("Added updated constraint chk_student_dept supporting 'AIML'.")
        except Exception as e:
            print("Error adding constraint chk_student_dept:", e)
            return

        # Prepare name pointer
        # Remove specific C406 names from general names pool
        general_names = [n for n in unique_names if n not in ["Rashvi", "Aaslin", "Charu Harinee", "Yamini"]]
        name_idx = 0
        
        # Room lists and required student counts
        # C101-C105: 6 each
        # C201-C205: 5 each
        # C301-C305: 4 each
        # C401-C405: 3 each
        floor_allocations = [
            # Floor 1
            ("C101", 6, 1), ("C102", 6, 1), ("C103", 6, 1), ("C104", 6, 1), ("C105", 6, 1),
            # Floor 2
            ("C201", 5, 2), ("C202", 5, 2), ("C203", 5, 2), ("C204", 5, 2), ("C205", 5, 2),
            # Floor 3
            ("C301", 4, 3), ("C302", 4, 3), ("C303", 4, 3), ("C304", 4, 3), ("C305", 4, 3),
            # Floor 4
            ("C401", 3, 4), ("C402", 3, 4), ("C403", 3, 4), ("C404", 3, 4), ("C405", 3, 4),
        ]
        
        departments_pool = ['CSE', 'AIDS', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL', 'MBA', 'MCA']
        
        created_count = 0
        room_assignments = {} # room_no -> [student names]
        
        reg_counter = 100
        phone_counter = 9876540000
        
        # Default password hash for 'password123'
        hashed_pwd = hash_password('password123')
        
        print("Inserting Floor 1-4 general students...")
        
        # 2. Insert Floor 1 to Floor 4 general students
        for room_no, count, year in floor_allocations:
            room_assignments[room_no] = []
            for _ in range(count):
                name = general_names[name_idx]
                name_idx += 1
                
                reg_no = f"22CS{reg_counter}"
                reg_counter += 1
                
                email = f"{name.lower().replace(' ', '')}{reg_counter}@hostelhub.com"
                phone = str(phone_counter)
                phone_counter += 1
                
                # Pick department from pool
                dept = departments_pool[created_count % len(departments_pool)]
                
                # Insert student record
                try:
                    execute_query("""
                        INSERT INTO students (name, register_number, email, password, phone, department, year, gender, room_no, address)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Female', %s, 'Hostel Hub Block C')
                    """, (name, reg_no, email, hashed_pwd, phone, dept, year, room_no))
                    
                    room_assignments[room_no].append(name)
                    created_count += 1
                except Exception as e:
                    print(f"Failed to insert general student '{name}': {e}")
                    
        # 3. Insert Special Room C406 students
        print("Inserting C406 special students...")
        room_assignments["C406"] = []
        for s_info in C406_STUDENTS:
            name = s_info['name']
            dept = s_info['dept']
            year = s_info['year']
            
            reg_no = f"22CS{reg_counter}"
            reg_counter += 1
            
            email = f"{name.lower().replace(' ', '')}@hostelhub.com"
            phone = str(phone_counter)
            phone_counter += 1
            
            try:
                execute_query("""
                    INSERT INTO students (name, register_number, email, password, phone, department, year, gender, room_no, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Female', 'C406', 'Hostel Hub Block C')
                """, (name, reg_no, email, hashed_pwd, phone, dept, year))
                
                room_assignments["C406"].append(name)
                created_count += 1
            except Exception as e:
                print(f"Failed to insert C406 student '{name}': {e}")
                
        # 4. Synchronize rooms.occupied column values
        print("Synchronizing rooms table occupied counts...")
        execute_query("UPDATE rooms r SET r.occupied = (SELECT COUNT(*) FROM students s WHERE s.room_no = r.room_no)")
        
        # Report results
        print("\n" + "="*50)
        print(" female student records population complete! ".upper().center(50, "="))
        print("="*50)
        print(f"Total Female Students Successfully Created: {created_count}")
        print("\nRoom-wise Student Assignment & Count:")
        for r_no in sorted(room_assignments.keys()):
            names_list = room_assignments[r_no]
            print(f"- Room {r_no} ({len(names_list)} students): {', '.join(names_list)}")
        print("="*50 + "\n")

if __name__ == '__main__':
    run_migration()
