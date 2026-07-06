import random
import sys

def delete_random_lines(input_file, output_file, p):
    """
    input_file: 입력 txt 파일 경로
    output_file: 출력 txt 파일 경로  
    p: 삭제 비율 (0.0 ~ 1.0)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 각 줄을 p 확률로 삭제 (줄바꿈 포함해서 버림)
    kept_lines = [line for line in lines if random.random() >= p]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(kept_lines)

    print(f"원본 줄 수: {len(lines)}")
    print(f"삭제된 줄 수: {len(lines) - len(kept_lines)}")
    print(f"남은 줄 수: {len(kept_lines)}")


if __name__ == "__main__":
    # 사용법: python script.py input.txt output.txt 0.3
    if len(sys.argv) == 4:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        ratio = float(sys.argv[3])
    else:
        # 직접 수정해서 사용
        input_path = "example.txt"
        output_path = "example1.txt"
        ratio = 0.6  # 30% 삭제

    if not (0.0 <= ratio <= 1.0):
        print("오류: p는 0.0~1.0 사이여야 합니다.")
        sys.exit(1)

    delete_random_lines(input_path, output_path, ratio)