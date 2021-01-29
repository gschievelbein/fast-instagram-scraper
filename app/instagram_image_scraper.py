import argparse
import pandas as pd
import os
from torpy.http.requests import TorRequests
import requests
import shutil
from func_timeout import func_timeout, FunctionTimedOut
from tqdm import tqdm


def load_dataframe(filename, image_name_column, image_link_column):
    df = pd.read_csv(open(filename, 'rb'), index_col=image_name_column, usecols=[image_name_column, image_link_column])
    df.index = df.index.astype(str)
    folder = os.path.basename(filename)
    folder = os.path.splitext(folder)[0]

    if not os.path.exists(folder):
        os.makedirs(folder)

    return df, folder


def remove_existing_images(i_img_dict, out_dir):
    files = os.listdir(out_dir)
    files = [os.path.splitext(file)[0] for file in files]
    for key in files:
        i_img_dict.pop(key)
    return i_img_dict


def tor_img_download_loop(i_img_dict, out_dir, headers):
    i_img_dict = remove_existing_images(i_img_dict, out_dir)
    if len(i_img_dict) > 0:
        with TorRequests() as tor_requests:
            with tor_requests.get_session() as sess:
                print("Image download tor circuit built.")
                for i, (k, v) in tqdm(enumerate(i_img_dict.items())):
                    download_img(sess, k, v, out_dir, headers)
    else:
        print('No new images do download')


def download_img(session, i_img_name, i_img_link, out_dir, headers):
    try:
        img_req = session.get(i_img_link, headers=headers, stream=True)  # fire request
        filename = os.path.join(out_dir, i_img_name)
        with open('{}.png'.format(filename), 'wb') as out_file:
            # saves png file always, if status is 200 file will have 1kb only
            shutil.copyfileobj(img_req.raw, out_file)
    except:
        print("Could't download image {} with link {}.".format(i_img_name, i_img_link))
        return "download_failed"


def download_images(d_img_dict, out_dir, headers, media_wait_between_requests):
    try:
        func_timeout(media_wait_between_requests, tor_img_download_loop, args=[d_img_dict, out_dir, headers])
    except FunctionTimedOut:
        print("Torsession terminated after {} seconds tor_timeout.".format(media_wait_between_requests))
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Name of source csv file', required=True)
    parser.add_argument('-n', '--name', help="Name of column with image names", default='shortcode')
    parser.add_argument('-l', '--link', help="Name of column with image urls", default='display_url')
    parser.add_argument('-w', '--request_wait', type=int, help='Waiting time between media requests', default=300)
    parser.add_argument('-a', '--user_agent', type=str, help='Change user agent if needed',
                        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/86.0.4240.198 Safari/537.36")

    args = parser.parse_args()

    headers = {'User-agent': args.user_agent}

    df, out_dir = load_dataframe(args.input, args.name, args.link)

    if not df.shape[0] == 0:
        url_dict = df.to_dict()[args.link]
        del df
        try:
            download_images(url_dict, out_dir, headers, args.request_wait)
            print('Finished :)')
        except FunctionTimedOut:
            print("Failed to download all images ):")
    else:
        print('Nothing to do (dataframe is empty o.O)')


if __name__ == "__main__":
    main()
