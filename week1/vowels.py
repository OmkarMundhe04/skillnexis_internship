s = input("Enter the string to get the vowels or consonants from :  ")
vowels = 0
consonants = 0

for i in s:
    if i.isalpha():
        if i.lower() in "aeiou":
            vowels += 1
        else:
            consonants += 1

print(f"The count of vowels and consonants is as follows \n vowels:  {vowels} \n consonants: {consonants}")
