import os
import xml.etree.ElementTree as ET
import shutil

classes = ["aeroplane","bicycle","bird","boat","bottle","bus","car","cat",
           "chair","cow","diningtable","dog","horse","motorbike","person",
           "pottedplant","sheep","sofa","train","tvmonitor"]

voc_path = "."

def convert(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x = (box[0] + box[1]) / 2.0 * dw
    y = (box[2] + box[3]) / 2.0 * dh
    w = (box[1] - box[0]) * dw
    h = (box[3] - box[2]) * dh
    return (x, y, w, h)

def convert_set(image_set):
    with open(f"{voc_path}/ImageSets/Main/{image_set}.txt") as f:
        image_ids = f.read().strip().split()

    for image_id in image_ids:
        xml_file = f"{voc_path}/Annotations/{image_id}.xml"
        img_file = f"{voc_path}/JPEGImages/{image_id}.jpg"

        tree = ET.parse(xml_file)
        root = tree.getroot()

        size = root.find("size")
        w = int(size.find("width").text)
        h = int(size.find("height").text)

        os.makedirs(f"dataset/images/{image_set}", exist_ok=True)
        os.makedirs(f"dataset/labels/{image_set}", exist_ok=True)

        with open(f"dataset/labels/{image_set}/{image_id}.txt", "w") as out:
            for obj in root.iter("object"):
                cls = obj.find("name").text
                if cls not in classes:
                    continue
                cls_id = classes.index(cls)

                xmlbox = obj.find("bndbox")
                b = (float(xmlbox.find("xmin").text),
                     float(xmlbox.find("xmax").text),
                     float(xmlbox.find("ymin").text),
                     float(xmlbox.find("ymax").text))

                bb = convert((w, h), b)
                out.write(f"{cls_id} {' '.join(map(str, bb))}\n")

        shutil.copy(img_file, f"dataset/images/{image_set}/{image_id}.jpg")

convert_set("train")
convert_set("val")