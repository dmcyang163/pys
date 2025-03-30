import cv2
try:
    import pyautogui
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
except:
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080

def show_resized(image, window_name="Panorama", max_ratio=0.8):
    """Display image resized to fit screen"""
    h, w = image.shape[:2]
    max_w = int(SCREEN_WIDTH * max_ratio)
    max_h = int(SCREEN_HEIGHT * max_ratio)
    
    scale = min(max_w/w, max_h/h)
    if scale < 1:
        image = cv2.resize(image, (int(w*scale), int(h*scale)))
    
    cv2.imshow(window_name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()