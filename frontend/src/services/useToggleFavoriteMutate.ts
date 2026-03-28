import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { authApi } from "@/configs/axios";
import { endpoint } from "@/configs/endpoint";
import type { UserFavorite } from "@/types/Stock";

export default function useToggleFavoriteMutate() {
	const token = localStorage.getItem("token");
	const queryClient = useQueryClient();

	return useMutation<
		void,
		Error,
		{ stockTicker: string; favorited: UserFavorite | undefined }
	>({
		mutationFn: async ({ stockTicker, favorited }) => {
			if (!token) throw new Error("You are not logged in.");

			if (favorited) {
				await authApi(token).delete(
					endpoint.watchlist.delete(favorited.id.toString()),
				);
			} else {
				await authApi(token).post(endpoint.watchlist.add, {
					stock_id: stockTicker,
				});
			}
		},
		onSuccess: async (_data, { stockTicker, favorited }) => {
			if (favorited) {
				toast.success(`${stockTicker} was removed from your favorites!`);
			} else {
				toast.success(`${stockTicker} was added to your favorites!`);
			}

			await queryClient.invalidateQueries({ queryKey: ["favorites"] });
		},
	});
}
