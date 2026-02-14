from collections import defaultdict
from typing import List


class Solution:
    def isPalindrome(self, s: str) -> bool:
        left = 0
        right = len(s) - 1

        while left < right:
            while left < right and not self.check_character(s[left]):
                left += 1

            while left < right and not self.check_character(s[right]):
                right -= 1

            left_c = s[left].lower()
            right_c = s[right].lower()
            if left_c != right_c:
                return False
            else:
                left += 1
                right -= 1

        return True

    def check_character(self, char):
        return ord('Z') >= ord(char) >= ord('A') or ord('z') >= ord(char) >= ord('a') or ord('9') >= ord(char) >= ord(
            '0')



qwe = [1,2,3]
nums = [10,11,11,12,12,12]
k = 2

a = []

a.append(qwe)
a.append(nums)


s = Solution()
qweqwe = s.isPalindrome("s.,")

print(qweqwe)