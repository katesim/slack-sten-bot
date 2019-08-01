from DBController import DBController


class Utils:

    @staticmethod
    def get_real_user_name(slack_client, user_id):
        user_info = slack_client.api_call("users.info", user=user_id)
        real_user_name = "user"
        if user_info.get("ok"):
            real_user_name = user_info.get("user").get("real_name")
            print('REAL NAME :', real_user_name, 'USER ID :', user_id)
        return real_user_name

    @staticmethod
    def get_real_channel_name(slack_client, channel_id):
        channel_info = slack_client.api_call("channels.info", channel=channel_id)
        real_channel_name = "Channel"
        if channel_info.get("ok"):
            real_channel_name = channel_info.get("channel").get("name")
            print('REAL CHANNEL NAME :', real_channel_name, 'CHANNEL ID :', channel_id)
        return real_channel_name

    @staticmethod
    def set_report_ts(slack_client, output_channel):
        real_channel_name = Utils.get_real_channel_name(slack_client, output_channel)
        response = slack_client.api_call("chat.postMessage",
                                         channel=output_channel,
                                         text="Update for *{}* work group".format(real_channel_name))
        ts = response["message"]["ts"]
        return ts

    @staticmethod
    def clear_reports_work_group(slack_client, work_group):
        work_group.clean_reports()
        work_group.update_ts(Utils.set_report_ts(slack_client, work_group.channel))
        print("REMOVE WG ")
        # pprint(work_group.reports)
        DBController.update_reports(work_group)
        return True
