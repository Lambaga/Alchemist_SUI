# Test demon images - create some simple placeholder frames
import pygame
import os

# Create demon pack directory if it doesn't exist
demon_pack_dir = r"d:\Alchemist\assets\Demon Pack"
os.makedirs(demon_pack_dir, exist_ok=True)

# Create 4 simple test demon frames
pygame.init()

for i in range(1, 5):
    # Create a 64x64 demon sprite
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    
    # Different colors for each frame to show animation
    colors = [(255, 100, 100), (255, 120, 120), (255, 140, 140), (255, 160, 160)]
    color = colors[i-1]
    
    # Draw a simple demon shape
    # Body
    pygame.draw.ellipse(surface, color, (16, 20, 32, 40))
    
    # Head  
    pygame.draw.circle(surface, color, (32, 20), 16)
    
    # Eyes (animation effect - slightly different positions)
    eye_offset = (i-1) * 2  # Eyes move slightly each frame
    pygame.draw.circle(surface, (255, 255, 0), (26 + eye_offset, 16), 4)
    pygame.draw.circle(surface, (255, 255, 0), (38 + eye_offset, 16), 4)
    
    # Horns
    pygame.draw.polygon(surface, (100, 0, 0), [(24, 8), (22, 4), (26, 6)])
    pygame.draw.polygon(surface, (100, 0, 0), [(40, 8), (38, 4), (42, 6)])
    
    # Save the frame
    filename = os.path.join(demon_pack_dir, f"Idle{i}.png")
    pygame.image.save(surface, filename)
    print(f"Created test demon frame: {filename}")

print("✅ Test demon frames created! You can replace these with your actual demon sprites.")
pygame.quit()
