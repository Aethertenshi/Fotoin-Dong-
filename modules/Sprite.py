import pygame

class TransformSprite:
    def __init__(self, image_path: str, x: float, y: float):
        """
        Initializes a transformable sprite.
        
        Parameters:
        - image_path: Path to the image file.
        - x: Initial X coordinate (center of the sprite).
        - y: Initial Y coordinate (center of the sprite).
        """
        # Load the image and ensure it has an alpha channel for transparency
        self.original_image = pygame.image.load(image_path).convert_alpha()
        
        self.x = x
        self.y = y
        self.alpha = 255          # Alpha value (0 to 255)
        self.rotation = 0.0        # Rotation in degrees (counter-clockwise)
        self.scale = 1.0           # Scale factor (1.0 is original size)

    def draw(self, screen: pygame.Surface, cover: bool = False):
        """
        Applies scaling, rotation, and alpha to the original image and draws it.
        
        Parameters:
        - screen: The surface to blit onto.
        - cover: If True, scales the image preserving aspect ratio to completely cover
                 the target screen, centering and cropping any excess.
        """
        if cover:
            target_width, target_height = screen.get_size()
            orig_width, orig_height = self.original_image.get_size()
            
            # Calculate scale factor to completely fill target surface (object-fit: cover)
            scale_x = target_width / orig_width
            scale_y = target_height / orig_height
            scale = max(scale_x, scale_y)
            
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            
            if new_width <= 0 or new_height <= 0:
                return
                
            # 1. Scale original image
            scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
            
            # 2. Crop centered subsurface to target resolution
            crop_x = (new_width - target_width) // 2
            crop_y = (new_height - target_height) // 2
            
            # Subsurface yields a cropped view sharing pixel data with parent
            cropped_image = scaled_image.subsurface((crop_x, crop_y, target_width, target_height))
            
            # 3. Apply Alpha Transparency
            cropped_image.set_alpha(max(0, min(255, int(self.alpha))))
            
            # 4. Draw centered to cover the screen
            screen.blit(cropped_image, (0, 0))
            return

        # Get original dimensions
        orig_width, orig_height = self.original_image.get_size()
        
        # Calculate new dimensions based on scale
        new_width = int(orig_width * self.scale)
        new_height = int(orig_height * self.scale)
        
        # Guard against zero or negative dimensions
        if new_width <= 0 or new_height <= 0:
            return

        # 1. Scale the image
        scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        
        # 2. Rotate the image (around its center)
        rotated_image = pygame.transform.rotate(scaled_image, self.rotation)
        
        # 3. Apply Alpha Transparency
        rotated_image.set_alpha(max(0, min(255, int(self.alpha))))
        
        # 4. Get the rect of the final image and center it at (self.x, self.y)
        rect = rotated_image.get_rect()
        rect.center = (int(self.x), int(self.y))
        
        # 5. Draw (blit) the image to the screen
        screen.blit(rotated_image, rect.topleft)
