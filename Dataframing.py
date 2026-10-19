import pandas as pd

# Aapke models aur image ke exact sequence ke mutabik columns ki list
columns = [
    'S.No.',
    'Name of Student',
    'Roll No.',
    'Mobile No.',
    'Email Id',
    'Your Educations',
    'Branch',
    'Passout Year',
    'Get Placement (Yes/No)',
    'If Yes Name of Placed Company',
    'Package in LPA',
    'Offer Letter Details',
    'Opted for Higher Studies (Yes/No)',
    'Institute Name',
    'Entrance Exam Details (CAT, GATE, OTHERS)',
    'Opted for Entrepreneurship/Self Employment',
    'Nature of Work',
    'Annual Turnover in LPA',
    'Others Preparing for Competitive Exam (UPSC, SSC, MPPSC, Banking, etc.)',
    'Not Engaged till Now (Yes/No)'
]

# Ek dummy row taaki format samajh me aa jaye
dummy_data = [{
    'S.No.': 1,
    'Name of Student': 'Rahul Sharma',
    'Roll No.': '24233C04043',
    'Mobile No.': '9876543210',
    'Email Id': 'rahul@example.com',
    'Your Educations': 'B.Tech',
    'Branch': 'CSE',
    'Passout Year': 2026,
    'Get Placement (Yes/No)': 'Yes',
    'If Yes Name of Placed Company': 'TCS',
    'Package in LPA': 4.50,
    'Offer Letter Details': 'Selected as System Engineer',
    'Opted for Higher Studies (Yes/No)': 'No',
    'Institute Name': '',
    'Entrance Exam Details (CAT, GATE, OTHERS)': '',
    'Opted for Entrepreneurship/Self Employment': 'No',
    'Nature of Work': '',
    'Annual Turnover in LPA': '',
    'Others Preparing for Competitive Exam (UPSC, SSC, MPPSC, Banking, etc.)': 'No',
    'Not Engaged till Now (Yes/No)': 'No'
}]

# DataFrame create karein aur Excel me save karein
df = pd.DataFrame(dummy_data, columns=columns)
file_name = 'students_data_template.xlsx'
df.to_excel(file_name, index=False)

print(f"✅ Perfect Excel file '{file_name}' successfully ban gayi hai!")
